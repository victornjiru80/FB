"""
Environmental Impact Reports PDF Export
"""
from django.http import HttpResponse
from .decorators import staff_member_required
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
from authentication.models import Donation, DonationAllocation
from custom_admin.impact_calculations import (
    calculate_food_waste_prevented,
    calculate_co2_saved,
    calculate_non_food_impact,
)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


@staff_member_required
def export_environmental_reports_pdf(request):
    """Export environmental impact reports to PDF"""
    # Get time period filter
    days = int(request.GET.get('days', 365))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get all accepted donations in the period
    all_donations = Donation.objects.filter(
        donated_at__gte=start_date,
        status='accepted'
    ).select_related('donor', 'foodbank')
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="environmental_impact_report_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=landscape(A4), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#10b981'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#059669'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    # Title
    elements.append(Paragraph('Environmental Impact Report', title_style))
    elements.append(Paragraph(f'Period: Last {days} days ({start_date.strftime("%Y-%m-%d")} to {timezone.now().strftime("%Y-%m-%d")})', styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # === CALCULATE METRICS ===
    donation_types = all_donations.values(
        'donation_type', 
        'donation_category', 
        'donation_mode'
    ).annotate(
        total_count=Count('id'),
        total_quantity=Sum('quantity'),
        total_subsidized_quantity=Sum('subsidized_quantity'),
        total_amount=Sum('amount')
    ).order_by('donation_category', 'donation_mode')
    
    total_food_donated_kg = 0
    total_subsidized_food_kg = 0
    total_non_food_units = 0
    total_co2_saved = 0
    total_waste_prevented = 0
    
    donation_details_data = [['#', 'Category', 'Mode', 'Count', 'Food (kg)', 'Subsidized (kg)', 'Non-Food', 'Waste Prevented (kg)', 'CO₂ Saved (tons)']]
    
    serial_no = 1
    for donation_type in donation_types:
        category = donation_type['donation_category']
        mode = donation_type['donation_mode']
        count = donation_type['total_count'] or 0
        quantity = donation_type['total_quantity'] or 0
        subsidized_qty = donation_type['total_subsidized_quantity'] or 0
        
        waste_prevented = 0
        co2_saved = 0
        
        if category == 'food':
            if mode == 'free':
                waste_prevented = quantity * 1.0
                total_food_donated_kg += quantity
            elif mode == 'subsidized':
                waste_prevented = subsidized_qty * 0.8
                total_subsidized_food_kg += subsidized_qty
            
            co2_saved = (waste_prevented * 2.5) / 1000
            total_waste_prevented += waste_prevented
            
        elif category == 'non_food':
            if mode == 'free':
                total_non_food_units += quantity
            elif mode == 'subsidized':
                total_non_food_units += subsidized_qty
            
            # Use shared dashboard methodology (same as views_impact)
            free_units = quantity if mode == 'free' else 0
            sub_units = subsidized_qty if mode == 'subsidized' else 0
            non_food_impact = calculate_non_food_impact(free_units, sub_units)
            waste_prevented = non_food_impact['waste_prevented_kg']
            co2_saved = non_food_impact['co2_saved_tons']
            total_waste_prevented += waste_prevented
        
        total_co2_saved += co2_saved
        
        donation_details_data.append([
            str(serial_no),
            category.title() if category else 'N/A',
            mode.title() if mode else 'N/A',
            str(count),
            f"{quantity:.2f}" if category == 'food' and mode == 'free' else '0',
            f"{subsidized_qty:.2f}" if category == 'food' and mode == 'subsidized' else '0',
            str(int(quantity if mode == 'free' else subsidized_qty)) if category == 'non_food' else '0',
            f"{waste_prevented:.2f}",
            f"{co2_saved:.3f}"
        ])
        serial_no += 1
    
    # === SUMMARY SECTION ===
    elements.append(Paragraph('Executive Summary', heading_style))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Donations', str(all_donations.count())],
        ['Total Food Donated (Free)', f"{total_food_donated_kg:.2f} kg"],
        ['Total Subsidized Food', f"{total_subsidized_food_kg:.2f} kg"],
        ['Total Waste Prevented', f"{total_waste_prevented:.2f} kg"],
        ['Total CO₂ Saved', f"{total_co2_saved:.3f} tons"],
        ['Non-Food Items Distributed', str(int(total_non_food_units))],
        ['Unique Donors', str(all_donations.values('donor').distinct().count())],
        ['Unique Foodbanks', str(all_donations.values('foodbank').distinct().count())],
    ]
    
    summary_table = Table(summary_data, colWidths=[3.5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # === DETAILED BREAKDOWN ===
    elements.append(Paragraph('Detailed Donation Breakdown', heading_style))
    
    donation_table = Table(donation_details_data, colWidths=[0.4*inch, 1*inch, 1*inch, 0.7*inch, 1*inch, 1.2*inch, 1*inch, 1.5*inch, 1.2*inch])
    donation_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(donation_table)
    elements.append(PageBreak())
    
    # === MONTHLY BREAKDOWN ===
    elements.append(Paragraph('Monthly Breakdown (Last 12 Months)', heading_style))
    
    monthly_data_list = [['Month', 'Food Donated (kg)', 'Subsidized (kg)', 'Waste Prevented (kg)', 'CO₂ Saved (tons)', 'Donations']]
    
    for i in range(12):
        month_start = timezone.now() - timedelta(days=30 * (11 - i))
        month_end = month_start + timedelta(days=30)
        
        month_donations = all_donations.filter(
            donated_at__gte=month_start,
            donated_at__lt=month_end
        )
        
        food_donations = month_donations.filter(donation_category='food')
        free_food = food_donations.filter(donation_mode='free').aggregate(total=Sum('quantity'))['total'] or 0
        subsidized_food = food_donations.filter(donation_mode='subsidized').aggregate(total=Sum('subsidized_quantity'))['total'] or 0
        
        waste_prevented = (free_food * 1.0) + (subsidized_food * 0.8)
        co2_saved = (waste_prevented * 2.5) / 1000
        
        monthly_data_list.append([
            month_start.strftime('%B %Y'),
            f"{free_food:.2f}",
            f"{subsidized_food:.2f}",
            f"{waste_prevented:.2f}",
            f"{co2_saved:.3f}",
            str(month_donations.count())
        ])
    
    monthly_table = Table(monthly_data_list, colWidths=[1.8*inch, 1.5*inch, 1.5*inch, 1.8*inch, 1.5*inch, 1*inch])
    monthly_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(monthly_table)
    elements.append(Spacer(1, 30))
    
    # === TOP CONTRIBUTORS ===
    elements.append(Paragraph('Top 10 Contributing Donors', heading_style))
    
    top_donors = all_donations.values('donor__email', 'donor__first_name', 'donor__last_name').annotate(
        total_donations=Count('id'),
        total_quantity=Sum('quantity'),
        total_amount=Sum('amount'),
        total_subsidized_value=Sum('subsidized_price'),
    ).order_by('-total_donations')[:10]
    
    donors_data = [['Rank', 'Donor', 'Donations', 'Quantity (kg)', 'Amount (KES)']]
    for idx, donor in enumerate(top_donors, 1):
        donor_name = f"{donor['donor__first_name'] or ''} {donor['donor__last_name'] or ''}".strip() or donor['donor__email'] or 'Anonymous'
        amt = donor['total_amount']
        sub_val = donor['total_subsidized_value']
        amount_str = f"{amt:.2f}" if amt else "—"
        if sub_val:
            amount_str += f" (Subsidized: {sub_val:.2f})"
        donors_data.append([
            str(idx),
            donor_name,
            str(donor['total_donations']),
            f"{donor['total_quantity'] or 0:.2f}",
            amount_str,
        ])
    
    donors_table = Table(donors_data, colWidths=[0.6*inch, 2.5*inch, 1*inch, 1.2*inch, 1.8*inch])
    donors_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(donors_table)
    
    # Build PDF
    doc.build(elements)
    return response
