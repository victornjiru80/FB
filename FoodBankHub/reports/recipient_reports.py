"""
Recipient-specific report views for FoodBankHub
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
import csv
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors

from authentication.models import (
    RequestManagement, DonationAllocation, RecipientProfile, Donation
)


@login_required
def recipient_requests_report(request):
    """Comprehensive requests report for recipients"""
    if request.user.user_type != 'RECIPIENT':
        return redirect('reports_dashboard')
    
    recipient_profile = request.user.recipient_profile
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get requests in date range
    requests = RequestManagement.objects.filter(
        recipient=recipient_profile,
        time_of_request__date__gte=start_dt,
        time_of_request__date__lte=end_dt
    ).select_related('foodbank', 'assigned_foodbank').order_by('-time_of_request')
    
    # Calculate statistics
    total_requests = requests.count()
    pending_requests = requests.filter(status='pending').count()
    fulfilled_requests = requests.filter(status='fulfilled').count()
    partial_requests = requests.filter(status='partial').count()
    declined_requests = requests.filter(status='declined').count()
    
    # Calculate total quantity requested and fulfilled
    total_quantity_requested = requests.aggregate(total=Sum('quantity'))['total'] or 0
    total_quantity_fulfilled = requests.aggregate(total=Sum('quantity_fulfilled'))['total'] or 0
    
    # Fulfillment rate
    fulfillment_rate = (fulfilled_requests / total_requests * 100) if total_requests > 0 else 0
    
    # Request type breakdown
    food_requests = requests.filter(request_type='food').count()
    non_food_requests = requests.filter(request_type='non_food').count()
    
    # Monthly breakdown
    monthly_data = requests.extra(
        select={'month': "DATE_TRUNC('month', time_of_request)"}
    ).values('month').annotate(
        count=Count('id'),
        fulfilled=Count('id', filter=Q(status='fulfilled'))
    ).order_by('month')
    
    # Foodbank breakdown
    foodbank_data = requests.filter(
        foodbank__isnull=False
    ).values('foodbank__foodbank_name').annotate(
        request_count=Count('id'),
        fulfilled_count=Count('id', filter=Q(status='fulfilled'))
    ).order_by('-request_count')
    
    context = {
        'requests': requests,
        'start_date': start_date,
        'end_date': end_date,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'fulfilled_requests': fulfilled_requests,
        'partial_requests': partial_requests,
        'declined_requests': declined_requests,
        'total_quantity_requested': total_quantity_requested,
        'total_quantity_fulfilled': total_quantity_fulfilled,
        'fulfillment_rate': fulfillment_rate,
        'food_requests': food_requests,
        'non_food_requests': non_food_requests,
        'monthly_data': monthly_data,
        'foodbank_data': foodbank_data,
    }
    
    return render(request, 'reports/recipient_requests_report.html', context)


@login_required
def recipient_allocations_report(request):
    """Report of donations allocated to recipient"""
    if request.user.user_type != 'RECIPIENT':
        return redirect('reports_dashboard')
    
    recipient_profile = request.user.recipient_profile
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get allocations
    allocations = DonationAllocation.objects.filter(
        recipient=recipient_profile,
        allocated_at__date__gte=start_dt,
        allocated_at__date__lte=end_dt
    ).select_related('donation', 'donation__donor', 'donation__foodbank').order_by('-allocated_at')
    
    # Calculate statistics
    total_allocations = allocations.count()
    acknowledged_allocations = allocations.filter(is_acknowledged=True).count()
    pending_acknowledgement = allocations.filter(is_acknowledged=False).count()
    
    # Calculate total value received
    total_amount_received = allocations.aggregate(total=Sum('amount'))['total'] or 0
    total_items_received = allocations.aggregate(total=Sum('quantity'))['total'] or 0
    
    # Donation type breakdown
    item_allocations = allocations.filter(donation__donation_type='item').count()
    money_allocations = allocations.filter(donation__donation_type='money').count()
    subsidized_allocations = allocations.filter(donation__donation_type='subsidized').count()
    
    # Monthly breakdown
    monthly_data = allocations.extra(
        select={'month': "DATE_TRUNC('month', allocated_at)"}
    ).values('month').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('month')
    
    # Foodbank breakdown
    foodbank_data = allocations.values(
        'donation__foodbank__foodbank_name'
    ).annotate(
        allocation_count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-allocation_count')
    
    context = {
        'allocations': allocations,
        'start_date': start_date,
        'end_date': end_date,
        'total_allocations': total_allocations,
        'acknowledged_allocations': acknowledged_allocations,
        'pending_acknowledgement': pending_acknowledgement,
        'total_amount_received': float(total_amount_received),
        'total_items_received': total_items_received,
        'item_allocations': item_allocations,
        'money_allocations': money_allocations,
        'subsidized_allocations': subsidized_allocations,
        'monthly_data': monthly_data,
        'foodbank_data': foodbank_data,
    }
    
    return render(request, 'reports/recipient_allocations_report.html', context)


@login_required
def export_recipient_requests_csv(request):
    """Export recipient requests as CSV"""
    if request.user.user_type != 'RECIPIENT':
        return redirect('reports_dashboard')
    
    recipient_profile = request.user.recipient_profile
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get requests
    requests = RequestManagement.objects.filter(
        recipient=recipient_profile,
        time_of_request__date__gte=start_dt,
        time_of_request__date__lte=end_dt
    ).select_related('foodbank', 'assigned_foodbank').order_by('-time_of_request')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="recipient_requests_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Request Type', 'Description', 'Quantity', 'Unit', 
        'Food Bank', 'Status', 'Quantity Fulfilled', 'Delivery Method', 'Location',
        'Decline Note'
    ])
    
    for req in requests:
        foodbank_name = req.foodbank.foodbank_name if req.foodbank else (
            req.assigned_foodbank.foodbank_name if req.assigned_foodbank else 'Anonymous'
        )
        writer.writerow([
            req.time_of_request.strftime('%Y-%m-%d %H:%M'),
            req.get_request_type_display(),
            req.description,
            req.quantity,
            req.unit,
            foodbank_name,
            req.get_status_display(),
            req.quantity_fulfilled,
            req.get_delivery_method_display(),
            req.location,
            (req.decline_message or '').strip()
        ])
    
    return response


@login_required
def export_recipient_requests_pdf(request):
    """Export recipient requests as PDF"""
    if request.user.user_type != 'RECIPIENT':
        return redirect('reports_dashboard')
    
    recipient_profile = request.user.recipient_profile
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get requests
    requests = RequestManagement.objects.filter(
        recipient=recipient_profile,
        time_of_request__date__gte=start_dt,
        time_of_request__date__lte=end_dt
    ).select_related('foodbank', 'assigned_foodbank').order_by('-time_of_request')
    
    # Calculate statistics
    total_requests = requests.count()
    fulfilled_requests = requests.filter(status='fulfilled').count()
    pending_requests = requests.filter(status='pending').count()
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1
    )
    story.append(Paragraph("Requests Report", title_style))
    story.append(Spacer(1, 20))
    
    # Recipient info
    story.append(Paragraph(f"<b>Recipient:</b> {recipient_profile.full_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Email:</b> {request.user.email}", styles['Normal']))
    story.append(Paragraph(f"<b>Period:</b> {start_date} to {end_date}", styles['Normal']))
    story.append(Paragraph(f"<b>Report Date:</b> {timezone.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Total Requests', str(total_requests)],
        ['Fulfilled Requests', str(fulfilled_requests)],
        ['Pending Requests', str(pending_requests)],
        ['Fulfillment Rate', f"{(fulfilled_requests / total_requests * 100):.1f}%" if total_requests > 0 else "0%"],
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # Requests table
    story.append(Paragraph("Request Details", styles['Heading2']))
    
    if requests:
        request_data = [['Date', 'Type', 'Description', 'Quantity', 'Food Bank', 'Status', 'Decline Note']]
        for req in requests:
            foodbank_name = req.foodbank.foodbank_name if req.foodbank else (
                req.assigned_foodbank.foodbank_name if req.assigned_foodbank else 'Anonymous'
            )
            desc = req.description[:40] + '...' if len(req.description) > 40 else req.description
            decline_note = (req.decline_message or '').strip()
            decline_note_display = decline_note[:40] + '...' if len(decline_note) > 43 else decline_note
            request_data.append([
                req.time_of_request.strftime('%Y-%m-%d'),
                req.get_request_type_display(),
                desc,
                f"{req.quantity} {req.unit}",
                foodbank_name[:20],
                req.get_status_display(),
                decline_note_display or '—'
            ])
        
        request_table = Table(request_data)
        request_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(request_table)
    else:
        story.append(Paragraph("No requests found for the selected period.", styles['Normal']))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recipient_requests_{start_date}_to_{end_date}.pdf"'
    
    return response


@login_required
def export_recipient_allocations_csv(request):
    """Export recipient allocations as CSV"""
    if request.user.user_type != 'RECIPIENT':
        return redirect('reports_dashboard')
    
    recipient_profile = request.user.recipient_profile
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get allocations
    allocations = DonationAllocation.objects.filter(
        recipient=recipient_profile,
        allocated_at__date__gte=start_dt,
        allocated_at__date__lte=end_dt
    ).select_related('donation', 'donation__donor', 'donation__foodbank').order_by('-allocated_at')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="recipient_allocations_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Donation Type', 'Food Bank', 'Donor', 'Quantity', 
        'Amount (KES)', 'Acknowledged', 'Item/Description'
    ])
    
    for allocation in allocations:
        donor_name = allocation.donation.donor.donor_profile.full_name if hasattr(allocation.donation.donor, 'donor_profile') else allocation.donation.donor.email
        item_desc = allocation.donation.item_name or allocation.donation.subsidized_product_type or 'N/A'
        
        writer.writerow([
            allocation.allocated_at.strftime('%Y-%m-%d %H:%M'),
            allocation.donation.get_donation_type_display(),
            allocation.donation.foodbank.foodbank_name,
            donor_name,
            allocation.quantity or 'N/A',
            allocation.amount or 'N/A',
            'Yes' if allocation.is_acknowledged else 'No',
            item_desc
        ])
    
    return response


@login_required
def export_recipient_allocations_pdf(request):
    """Export recipient allocations as PDF"""
    if request.user.user_type != 'RECIPIENT':
        return redirect('reports_dashboard')
    
    recipient_profile = request.user.recipient_profile
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get allocations
    allocations = DonationAllocation.objects.filter(
        recipient=recipient_profile,
        allocated_at__date__gte=start_dt,
        allocated_at__date__lte=end_dt
    ).select_related('donation', 'donation__donor', 'donation__foodbank').order_by('-allocated_at')
    
    # Calculate statistics
    total_allocations = allocations.count()
    total_amount = allocations.aggregate(total=Sum('amount'))['total'] or 0
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1
    )
    story.append(Paragraph("Allocations Report", title_style))
    story.append(Spacer(1, 20))
    
    # Recipient info
    story.append(Paragraph(f"<b>Recipient:</b> {recipient_profile.full_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Email:</b> {request.user.email}", styles['Normal']))
    story.append(Paragraph(f"<b>Period:</b> {start_date} to {end_date}", styles['Normal']))
    story.append(Paragraph(f"<b>Report Date:</b> {timezone.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Total Allocations', str(total_allocations)],
        ['Total Amount Received (KES)', f"{total_amount:,.2f}"],
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # Allocations table
    story.append(Paragraph("Allocation Details", styles['Heading2']))
    
    if allocations:
        allocation_data = [['Date', 'Type', 'Food Bank', 'Quantity', 'Amount (KES)', 'Acknowledged']]
        for allocation in allocations:
            allocation_data.append([
                allocation.allocated_at.strftime('%Y-%m-%d'),
                allocation.donation.get_donation_type_display(),
                allocation.donation.foodbank.foodbank_name[:20],
                str(allocation.quantity) if allocation.quantity else 'N/A',
                f"{allocation.amount:,.2f}" if allocation.amount else 'N/A',
                'Yes' if allocation.is_acknowledged else 'No'
            ])
        
        allocation_table = Table(allocation_data)
        allocation_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(allocation_table)
    else:
        story.append(Paragraph("No allocations found for the selected period.", styles['Normal']))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recipient_allocations_{start_date}_to_{end_date}.pdf"'
    
    return response
