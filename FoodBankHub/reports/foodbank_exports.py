"""
Additional CSV export functions for foodbank reports
"""
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
import csv

from authentication.models import Donation, FoodBankRequest
from .export_utils import donation_amount_display, donation_item_desc, donation_qty_display, fmt_dt


@login_required
def export_foodbank_donations_received_csv(request):
    """Export foodbank donations received as CSV"""
    if request.user.user_type != 'FOODBANK':
        return redirect('reports_dashboard')
    
    foodbank_profile = request.user.foodbank_profile
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get donations
    donations = Donation.objects.filter(
        foodbank=foodbank_profile,
        donated_at__date__gte=start_dt,
        donated_at__date__lte=end_dt
    ).select_related('donor', 'donor__donor_profile', 'foodbank_request').order_by('-donated_at')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="donations_received_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Donor Name', 'Donor Email', 'Type', 'Category', 'Item/Description', 
        'Quantity', 'Amount (KES)', 'Request Title', 'Status', 'Delivery Method', 'Message'
    ])
    
    for donation in donations:
        donor_name = donation.donor.donor_profile.full_name if hasattr(donation.donor, 'donor_profile') else 'N/A'
        item_desc = donation_item_desc(donation)
        quantity = donation_qty_display(donation)
        amount = donation_amount_display(donation)
        request_title = donation.foodbank_request.title if donation.foodbank_request else 'General Donation'
        
        writer.writerow([
            fmt_dt(donation.donated_at),
            donor_name,
            donation.donor.email,
            donation.get_donation_type_display(),
            donation.get_donation_category_display(),
            item_desc,
            quantity,
            amount,
            request_title,
            donation.get_status_display(),
            donation.get_delivery_method_display() if donation.delivery_method else 'N/A',
            donation.message or 'N/A'
        ])
    
    return response


@login_required
def export_foodbank_request_fulfillment_csv(request):
    """Export foodbank request fulfillment as CSV"""
    if request.user.user_type != 'FOODBANK':
        return redirect('reports_dashboard')
    
    foodbank_profile = request.user.foodbank_profile
    
    # Get all requests
    requests = FoodBankRequest.objects.filter(
        foodbank=foodbank_profile
    ).order_by('-created_at')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="request_fulfillment_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Created Date', 'Title', 'Description', 'Donation Type', 'Priority', 
        'Status', 'Quantity Needed', 'Unit', 'Donations Received', 
        'Unique Donors', 'Fulfillment %', 'Deadline'
    ])
    
    for req in requests:
        donations_count = req.donations.count()
        unique_donors = req.donations.values('donor').distinct().count()
        fulfillment_pct = req.get_fulfillment_percentage()
        
        writer.writerow([
            req.created_at.strftime('%Y-%m-%d %H:%M'),
            req.title,
            req.description,
            req.get_donation_type_display(),
            req.get_priority_display(),
            req.get_status_display(),
            req.quantity_needed or 'N/A',
            req.quantity_unit or 'N/A',
            donations_count,
            unique_donors,
            f"{fulfillment_pct:.1f}%",
            req.deadline.strftime('%Y-%m-%d') if req.deadline else 'N/A'
        ])
    
    return response
