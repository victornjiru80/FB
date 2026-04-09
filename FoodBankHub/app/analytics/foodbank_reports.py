"""
Comprehensive FoodBank Reports Module
Contains all report views and export functions for foodbank users
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, Avg
from django.db.models.functions import TruncMonth, TruncDay, TruncWeek
from django.core.paginator import Paginator
from django.contrib import messages
from datetime import datetime, timedelta
from authentication.models import (
    Donation, FoodBankRequest, FoodBankProfile, 
    SubscriptionPayment, FoodBankSubscription, DonationAllocation
)
import csv
import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


@login_required
def foodbank_reports_dashboard(request):
    """Main reports dashboard - accessible to all users"""
    context = {'user_type': request.user.user_type}
    
    if request.user.user_type == 'FOODBANK':
        foodbank_profile = request.user.foodbank_profile
        
        # Get date range (default to last 30 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Quick stats for dashboard
        total_donations = Donation.objects.filter(foodbank=foodbank_profile).count()
        total_revenue = Donation.objects.filter(
            foodbank=foodbank_profile, 
            donation_type='money'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_requests = FoodBankRequest.objects.filter(foodbank=foodbank_profile).count()
        fulfilled_requests = FoodBankRequest.objects.filter(
            foodbank=foodbank_profile, 
            status='fulfilled'
        ).count()
        
        total_allocations = DonationAllocation.objects.filter(
            donation__foodbank=foodbank_profile
        ).count()
        
        pending_donations = Donation.objects.filter(
            foodbank=foodbank_profile,
            status='pending'
        ).count()
        
        # Subscription info
        subscription = FoodBankSubscription.objects.filter(foodbank=foodbank_profile).first()
        
        context.update({
            'total_donations': total_donations,
            'total_revenue': total_revenue,
            'total_requests': total_requests,
            'fulfilled_requests': fulfilled_requests,
            'fulfillment_rate': (fulfilled_requests / total_requests * 100) if total_requests > 0 else 0,
            'total_allocations': total_allocations,
            'pending_donations': pending_donations,
            'subscription': subscription,
        })
    
    elif request.user.user_type == 'DONOR':
        # Donor-specific stats
        donor_profile = request.user.donor_profile
        
        # Total donations made by this donor
        my_donations = Donation.objects.filter(donor=request.user)
        total_donations_made = my_donations.count()
        
        # Total monetary donations
        total_money_donated = my_donations.filter(
            donation_type='money'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Total items donated
        total_items_donated = my_donations.filter(
            donation_type='item'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Accepted donations
        accepted_donations = my_donations.filter(status='accepted').count()
        
        # Pending donations
        pending_donations = my_donations.filter(status='pending').count()
        
        # Foodbanks helped
        foodbanks_helped = my_donations.values('foodbank').distinct().count()
        
        context.update({
            'total_donations_made': total_donations_made,
            'total_money_donated': total_money_donated,
            'total_items_donated': total_items_donated,
            'accepted_donations': accepted_donations,
            'pending_donations': pending_donations,
            'foodbanks_helped': foodbanks_helped,
        })
    
    else:
        # Recipient-specific stats
        recipient_profile = request.user.recipient_profile
        
        # Get all allocations for this recipient
        my_allocations = DonationAllocation.objects.filter(recipient=recipient_profile)
        total_allocations = my_allocations.count()
        
        # Total items received
        total_items_received = my_allocations.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Subsidized donations claimed
        subsidized_claimed = my_allocations.filter(
            donation__donation_type='subsidized'
        ).count()
        
        # Regular donations received
        regular_donations = my_allocations.filter(
            donation__donation_type='item'
        ).count()
        
        # Foodbanks supported by
        foodbanks_count = my_allocations.values('donation__foodbank').distinct().count()
        
        context.update({
            'total_allocations': total_allocations,
            'total_items_received': total_items_received,
            'subsidized_claimed': subsidized_claimed,
            'regular_donations': regular_donations,
            'foodbanks_count': foodbanks_count,
        })
    
    return render(request, 'reports/foodbank_dashboard.html', context)


@login_required
def donations_revenue_report(request):
    """Comprehensive donations and revenue report"""
    if request.user.user_type != 'FOODBANK':
        messages.warning(request, 'This report is designed for foodbank users.')
        return redirect('foodbank_reports_dashboard')
    
    foodbank_profile = request.user.foodbank_profile
    
    # Get filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    donation_type = request.GET.get('donation_type', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    
    # Default date range (last 30 days)
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    # Base queryset
    donations = Donation.objects.filter(
        foodbank=foodbank_profile,
        donated_at__date__gte=start_date,
        donated_at__date__lte=end_date
    ).select_related('donor', 'donor__donor_profile').order_by('-donated_at')
    
    # Apply filters
    if donation_type:
        donations = donations.filter(donation_type=donation_type)
    if category:
        donations = donations.filter(donation_category=category)
    if status:
        donations = donations.filter(status=status)
    
    # Calculate metrics
    total_donations = donations.count()
    total_revenue = donations.filter(donation_type='money').aggregate(
        total=Sum('amount'))['total'] or 0
    total_items = donations.filter(donation_type='item').aggregate(
        total=Sum('quantity'))['total'] or 0
    subsidized_revenue = donations.filter(donation_type='subsidized').aggregate(
        total=Sum('subsidized_price'))['total'] or 0
    
    # Top donors
    top_donors = donations.values(
        'donor__email', 
        'donor__donor_profile__full_name'
    ).annotate(
        donation_count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-donation_count')[:10]
    
    # Monthly trends
    monthly_data = donations.annotate(
        month=TruncMonth('donated_at')
    ).values('month').annotate(
        count=Count('id'),
        revenue=Sum('amount')
    ).order_by('month')
    
    # Category breakdown
    category_breakdown = donations.values('donation_category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Pagination
    paginator = Paginator(donations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'donations': page_obj,
        'page_obj': page_obj,
        'total_donations': total_donations,
        'total_revenue': total_revenue,
        'total_items': total_items,
        'subsidized_revenue': subsidized_revenue,
        'top_donors': top_donors,
        'monthly_data': list(monthly_data),
        'category_breakdown': list(category_breakdown),
        'start_date': start_date,
        'end_date': end_date,
        'selected_type': donation_type,
        'selected_category': category,
        'selected_status': status,
    }
    
    return render(request, 'reports/donations_revenue_report.html', context)


@login_required
def inventory_distribution_report(request):
    """Inventory status and distribution report"""
    if request.user.user_type != 'FOODBANK':
        messages.warning(request, 'This report is designed for foodbank users.')
        return redirect('foodbank_reports_dashboard')
    
    foodbank_profile = request.user.foodbank_profile
    
    # Get all item donations
    item_donations = Donation.objects.filter(
        foodbank=foodbank_profile,
        donation_type='item',
        status='accepted'
    ).select_related('donor', 'donor__donor_profile')
    
    # Calculate available vs allocated
    total_items = item_donations.count()
    allocated_items = item_donations.filter(is_allocated=True).count()
    unallocated_items = total_items - allocated_items
    
    # Get allocations
    allocations = DonationAllocation.objects.filter(
        donation__foodbank=foodbank_profile
    ).select_related('donation', 'recipient', 'recipient__user').order_by('-allocated_at')
    
    # Distribution by recipient
    recipient_distribution = allocations.values(
        'recipient__full_name'
    ).annotate(
        count=Count('id'),
        total_quantity=Sum('quantity')
    ).order_by('-count')[:10]
    
    # Monthly distribution trends
    monthly_distribution = allocations.annotate(
        month=TruncMonth('allocated_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Category-wise inventory
    category_inventory = item_donations.values('donation_category').annotate(
        total=Count('id'),
        allocated=Count('id', filter=Q(is_allocated=True)),
        available=Count('id', filter=Q(is_allocated=False))
    ).order_by('-total')
    
    # Pagination for allocations
    paginator = Paginator(allocations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'total_items': total_items,
        'allocated_items': allocated_items,
        'unallocated_items': unallocated_items,
        'allocation_rate': (allocated_items / total_items * 100) if total_items > 0 else 0,
        'allocations': page_obj,
        'page_obj': page_obj,
        'recipient_distribution': list(recipient_distribution),
        'monthly_distribution': list(monthly_distribution),
        'category_inventory': list(category_inventory),
    }
    
    return render(request, 'reports/inventory_distribution_report.html', context)


@login_required
def requests_fulfillment_report(request):
    """Requests and fulfillment tracking report"""
    if request.user.user_type != 'FOODBANK':
        messages.warning(request, 'This report is designed for foodbank users.')
        return redirect('foodbank_reports_dashboard')
    
    foodbank_profile = request.user.foodbank_profile
    
    # Get filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status_filter = request.GET.get('status', '')
    
    # Default date range
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    # Get requests
    requests = FoodBankRequest.objects.filter(
        foodbank=foodbank_profile,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).select_related('recipient', 'recipient__user').order_by('-created_at')
    
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    # Calculate metrics
    total_requests = requests.count()
    fulfilled_requests = requests.filter(status='fulfilled').count()
    pending_requests = requests.filter(status='pending').count()
    cancelled_requests = requests.filter(status='cancelled').count()
    
    fulfillment_rate = (fulfilled_requests / total_requests * 100) if total_requests > 0 else 0
    
    # Average response time (for fulfilled requests)
    fulfilled_with_dates = requests.filter(
        status='fulfilled',
        fulfilled_at__isnull=False
    )
    
    avg_response_time = None
    if fulfilled_with_dates.exists():
        total_seconds = sum([
            (req.fulfilled_at - req.created_at).total_seconds() 
            for req in fulfilled_with_dates
        ])
        avg_response_time = total_seconds / fulfilled_with_dates.count() / 3600  # Convert to hours
    
    # Monthly trends
    monthly_requests = requests.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Count('id'),
        fulfilled=Count('id', filter=Q(status='fulfilled'))
    ).order_by('month')
    
    # Top recipients
    top_recipients = requests.values(
        'recipient__full_name'
    ).annotate(
        request_count=Count('id'),
        fulfilled_count=Count('id', filter=Q(status='fulfilled'))
    ).order_by('-request_count')[:10]
    
    # Pagination
    paginator = Paginator(requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requests': page_obj,
        'page_obj': page_obj,
        'total_requests': total_requests,
        'fulfilled_requests': fulfilled_requests,
        'pending_requests': pending_requests,
        'cancelled_requests': cancelled_requests,
        'fulfillment_rate': fulfillment_rate,
        'avg_response_time': avg_response_time,
        'monthly_requests': list(monthly_requests),
        'top_recipients': list(top_recipients),
        'start_date': start_date,
        'end_date': end_date,
        'selected_status': status_filter,
    }
    
    return render(request, 'reports/requests_fulfillment_report.html', context)


@login_required
def subscription_financial_report(request):
    """Subscription and financial summary report"""
    if request.user.user_type != 'FOODBANK':
        messages.warning(request, 'This report is designed for foodbank users.')
        return redirect('foodbank_reports_dashboard')
    
    foodbank_profile = request.user.foodbank_profile
    
    # Get subscription
    subscription = FoodBankSubscription.objects.filter(foodbank=foodbank_profile).first()
    
    # Get payment history
    payments = SubscriptionPayment.objects.filter(
        foodbank=foodbank_profile
    ).select_related('verified_by').order_by('-submitted_at')
    
    # Calculate metrics
    total_paid = payments.filter(status='approved').aggregate(
        total=Sum('amount'))['total'] or 0
    pending_payments = payments.filter(status='pending').count()
    approved_payments = payments.filter(status='approved').count()
    rejected_payments = payments.filter(status='rejected').count()
    
    # Monthly payment trends
    monthly_payments = payments.filter(status='approved').annotate(
        month=TruncMonth('submitted_at')
    ).values('month').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('month')
    
    # Donation revenue
    donation_revenue = Donation.objects.filter(
        foodbank=foodbank_profile,
        donation_type='money'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    subsidized_revenue = Donation.objects.filter(
        foodbank=foodbank_profile,
        donation_type='subsidized',
        status='accepted'
    ).aggregate(total=Sum('subsidized_price'))['total'] or 0
    
    # Total financial summary
    total_revenue = donation_revenue + subsidized_revenue
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'subscription': subscription,
        'payments': page_obj,
        'page_obj': page_obj,
        'total_paid': total_paid,
        'pending_payments': pending_payments,
        'approved_payments': approved_payments,
        'rejected_payments': rejected_payments,
        'monthly_payments': list(monthly_payments),
        'donation_revenue': donation_revenue,
        'subsidized_revenue': subsidized_revenue,
        'total_revenue': total_revenue,
    }
    
    return render(request, 'reports/subscription_financial_report.html', context)


@login_required
def impact_analytics_report(request):
    """Impact dashboard and analytics"""
    if request.user.user_type != 'FOODBANK':
        messages.warning(request, 'This report is designed for foodbank users.')
        return redirect('foodbank_reports_dashboard')
    
    foodbank_profile = request.user.foodbank_profile
    
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=90)  # Last 3 months
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    # Total beneficiaries (unique recipients)
    total_beneficiaries = DonationAllocation.objects.filter(
        donation__foodbank=foodbank_profile,
        allocated_at__date__gte=start_date,
        allocated_at__date__lte=end_date
    ).values('recipient').distinct().count()
    
    # Items distributed
    items_distributed = DonationAllocation.objects.filter(
        donation__foodbank=foodbank_profile,
        allocated_at__date__gte=start_date,
        allocated_at__date__lte=end_date
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    # Monetary value of assistance
    monetary_assistance = Donation.objects.filter(
        foodbank=foodbank_profile,
        donation_type='money',
        donated_at__date__gte=start_date,
        donated_at__date__lte=end_date
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Total donations received
    total_donations = Donation.objects.filter(
        foodbank=foodbank_profile,
        donated_at__date__gte=start_date,
        donated_at__date__lte=end_date
    ).count()
    
    # Unique donors
    unique_donors = Donation.objects.filter(
        foodbank=foodbank_profile,
        donated_at__date__gte=start_date,
        donated_at__date__lte=end_date
    ).values('donor').distinct().count()
    
    # Requests fulfilled
    requests_fulfilled = FoodBankRequest.objects.filter(
        foodbank=foodbank_profile,
        status='fulfilled',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).count()
    
    # Weekly trends
    weekly_impact = DonationAllocation.objects.filter(
        donation__foodbank=foodbank_profile,
        allocated_at__date__gte=start_date,
        allocated_at__date__lte=end_date
    ).annotate(
        week=TruncWeek('allocated_at')
    ).values('week').annotate(
        beneficiaries=Count('recipient', distinct=True),
        items=Sum('quantity')
    ).order_by('week')
    
    # Category-wise impact
    category_impact = Donation.objects.filter(
        foodbank=foodbank_profile,
        donated_at__date__gte=start_date,
        donated_at__date__lte=end_date
    ).values('donation_category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total_beneficiaries': total_beneficiaries,
        'items_distributed': items_distributed,
        'monetary_assistance': monetary_assistance,
        'total_donations': total_donations,
        'unique_donors': unique_donors,
        'requests_fulfilled': requests_fulfilled,
        'weekly_impact': list(weekly_impact),
        'category_impact': list(category_impact),
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/impact_analytics_report.html', context)
