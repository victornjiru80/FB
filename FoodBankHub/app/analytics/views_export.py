from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from authentication.models import RequestManagement, UnspecifiedDonationManagement, Donation
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from decimal import Decimal


@login_required
def export_completed_requests_pdf(request):
    """Export completed requests to PDF"""
    if request.user.user_type != 'RECIPIENT':
        return redirect('dashboard')
    
    recipient_profile = request.user.recipient_profile
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get completed requests
    completed_requests = RequestManagement.objects.filter(
        recipient=recipient_profile,
        status='fulfilled',
        acknowledged_by_recipient=True,
        additional_notes__icontains='Receipt Confirmed',
        time_of_request__date__gte=start_dt,
        time_of_request__date__lte=end_dt
    ).select_related('foodbank', 'assigned_foodbank').order_by('-time_of_request')
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#06b6d4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph(f"Completed Requests Report", title_style))
    story.append(Paragraph(f"Recipient: {recipient_profile.full_name}", styles['Normal']))
    story.append(Paragraph(f"Period: {start_date} to {end_date}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Table data
    data = [['S/No', 'Date', 'Type', 'Description', 'Food Bank', 'Qty', 'Unit', 'Status', 'Fulfilled']]
    
    for idx, req in enumerate(completed_requests, 1):
        foodbank = req.foodbank.foodbank_name if req.foodbank else (
            req.assigned_foodbank.foodbank_name if req.assigned_foodbank else 'Anonymous'
        )
        
        data.append([
            str(idx),
            req.time_of_request.strftime('%m/%d/%Y'),
            req.get_request_type_display(),
            req.description[:40] + '...' if len(req.description) > 40 else req.description,
            foodbank[:20],
            str(req.quantity),
            req.get_unit_display(),
            req.get_status_display(),
            req.fulfilled_at.strftime('%m/%d/%Y') if req.fulfilled_at else 'N/A'
        ])
    
    # Create table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#06b6d4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Total Completed Requests: {completed_requests.count()}", styles['Normal']))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="completed_requests_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response


@login_required
def export_completed_unspecified_pdf(request):
    """Export completed unspecified donations to PDF"""
    if request.user.user_type != 'RECIPIENT':
        return redirect('dashboard')
    
    recipient_profile = request.user.recipient_profile
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get completed unspecified donations
    completed_unspecified = UnspecifiedDonationManagement.objects.filter(
        accepted_by_recipient=recipient_profile,
        recipient_status='received',
        created_at__date__gte=start_dt,
        created_at__date__lte=end_dt
    ).select_related('donation', 'donation__donor', 'donation__foodbank').order_by('-created_at')
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#06b6d4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph(f"Completed Unspecified Donations Report", title_style))
    story.append(Paragraph(f"Recipient: {recipient_profile.full_name}", styles['Normal']))
    story.append(Paragraph(f"Period: {start_date} to {end_date}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Table data
    data = [['S/No', 'Donation Date', 'Donor', 'Food Bank', 'Item Type', 'Quantity', 'Accepted Date']]
    
    for idx, item in enumerate(completed_unspecified, 1):
        donor = item.donation.donor.get_full_name() if item.donation.donor else 'Anonymous'
        
        data.append([
            str(idx),
            item.donation.donated_at.strftime('%m/%d/%Y'),
            donor[:20],
            item.donation.foodbank.foodbank_name[:20],
            item.donation.get_item_type_display() if hasattr(item.donation, 'get_item_type_display') else 'Food Item',
            f"{item.donation.quantity} {item.donation.get_quantity_unit_display() if hasattr(item.donation, 'get_quantity_unit_display') else ''}",
            item.created_at.strftime('%m/%d/%Y')
        ])
    
    # Create table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#06b6d4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Total Completed Unspecified Donations: {completed_unspecified.count()}", styles['Normal']))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="completed_unspecified_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response


@login_required
def export_completed_subsidized_pdf(request):
    """Export completed subsidized donations to PDF"""
    if request.user.user_type != 'RECIPIENT':
        return redirect('dashboard')
    
    recipient_profile = request.user.recipient_profile
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get completed subsidized donations
    completed_subsidized = Donation.objects.filter(
        donation_type='subsidized',
        accepted_by_recipient=recipient_profile,
        delivery_status='delivered',
        donated_at__date__gte=start_dt,
        donated_at__date__lte=end_dt
    ).select_related('donor', 'foodbank').order_by('-donated_at')
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#06b6d4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph(f"Completed Subsidized Donations Report", title_style))
    story.append(Paragraph(f"Recipient: {recipient_profile.full_name}", styles['Normal']))
    story.append(Paragraph(f"Period: {start_date} to {end_date}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Table data
    data = [['S/No', 'Date', 'Donor', 'Food Bank', 'Product', 'Qty', 'Original (KES)', 'Subsidized (KES)', 'Discount %']]
    
    for idx, donation in enumerate(completed_subsidized, 1):
        donor = donation.donor.get_full_name() if donation.donor else 'Anonymous'
        
        # Calculate discount
        discount = ''
        if donation.subsidized_discount_percentage:
            discount = f"{float(donation.subsidized_discount_percentage):.0f}%"
        elif donation.subsidized_market_price and donation.subsidized_price:
            market = float(donation.subsidized_market_price)
            subsidized = float(donation.subsidized_price)
            if market > 0:
                calc_discount = ((market - subsidized) / market) * 100
                discount = f"{calc_discount:.0f}%"
        
        data.append([
            str(idx),
            donation.donated_at.strftime('%m/%d/%Y'),
            donor[:15],
            donation.foodbank.foodbank_name[:15],
            (donation.subsidized_product_type or 'N/A')[:20],
            f"{donation.subsidized_quantity or donation.quantity}",
            f"{float(donation.subsidized_market_price):.2f}" if donation.subsidized_market_price else 'N/A',
            f"{float(donation.subsidized_price or donation.amount):.2f}",
            discount or '-'
        ])
    
    # Create table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#06b6d4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    # Summary
    total_saved = sum([
        float(d.subsidized_market_price or 0) - float(d.subsidized_price or d.amount or 0)
        for d in completed_subsidized
        if d.subsidized_market_price and (d.subsidized_price or d.amount)
    ])
    
    story.append(Paragraph(f"Total Completed Subsidized Donations: {completed_subsidized.count()}", styles['Normal']))
    story.append(Paragraph(f"Total Amount Saved: KES {total_saved:,.2f}", styles['Normal']))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="completed_subsidized_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response
