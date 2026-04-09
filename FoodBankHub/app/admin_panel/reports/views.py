from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncMonth, TruncDay
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime, timedelta
from authentication.models import (
    Donation, FoodBankRequest, CustomUser, FoodBankProfile, 
    DonorProfile, Notification, PaymentTransaction
)
import json
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from io import BytesIO


@login_required
def reports_dashboard(request):
    """Main reports dashboard with available report types"""
    user_type = request.user.user_type
    
    # Get basic stats for dashboard
    if user_type == 'DONOR':
        from authentication.models import DonationDiscussion
        
        # Get date range from request
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Default to last 6 months if no dates provided
        if not start_date:
            start_date = (timezone.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = timezone.now().strftime('%Y-%m-%d')
        
        # Convert to datetime objects
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get all donations (lifetime)
        all_donations = Donation.objects.filter(donor=request.user)
        
        # Get donations in date range
        donations = all_donations.filter(
            donated_at__date__gte=start_dt,
            donated_at__date__lte=end_dt
        ).select_related('foodbank', 'foodbank_request').order_by('-donated_at')
        
        # Lifetime statistics
        lifetime_donations = all_donations.count()
        lifetime_amount = all_donations.filter(donation_type='money').aggregate(
            total=Sum('amount'))['total'] or 0
        lifetime_subsidized_value = all_donations.filter(donation_type='subsidized').aggregate(
            total=Sum('amount'))['total'] or 0
        lifetime_foodbanks = all_donations.values('foodbank').distinct().count()
        
        # Period statistics
        total_donations = donations.count()
        total_amount = donations.filter(donation_type='money').aggregate(
            total=Sum('amount'))['total'] or 0
        total_items = donations.filter(donation_type='item').count()
        total_subsidized = donations.filter(donation_type='subsidized').count()
        total_csr = donations.filter(donation_type='csr').count()
        total_other = donations.filter(donation_type='other').count()
        foodbanks_helped = donations.values('foodbank').distinct().count()
        
        # Donation status breakdown
        pending_donations = donations.filter(status='pending').count()
        accepted_donations = donations.filter(status='accepted').count()
        declined_donations = donations.filter(status='declined').count()
        
        # Discussion statistics
        total_discussions = DonationDiscussion.objects.filter(donor=request.user).count()
        active_discussions = DonationDiscussion.objects.filter(
            donor=request.user, status='in_progress'
        ).count()
        
        # Monthly breakdown
        monthly_data = donations.annotate(
            month=TruncMonth('donated_at')
        ).values('month').annotate(
            count=Count('id'),
            amount=Sum('amount')
        ).order_by('month')
        
        # Food bank breakdown
        foodbank_data = donations.values('foodbank__foodbank_name').annotate(
            count=Count('id'),
            amount=Sum('amount')
        ).order_by('-count')[:10]
        
        # Donation type breakdown
        type_breakdown = donations.values('donation_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        context = {
            'user_type': user_type,
            'donations': donations[:20],  # Recent 20 for preview
            'start_date': start_date,
            'end_date': end_date,
            
            # Lifetime stats
            'lifetime_donations': lifetime_donations,
            'lifetime_amount': float(lifetime_amount),
            'lifetime_subsidized_value': float(lifetime_subsidized_value),
            'lifetime_total_value': float(lifetime_amount + lifetime_subsidized_value),
            'lifetime_foodbanks': lifetime_foodbanks,
            
            # Period stats
            'total_donations': total_donations,
            'total_amount': float(total_amount),
            'total_items': total_items,
            'total_subsidized': total_subsidized,
            'total_csr': total_csr,
            'total_other': total_other,
            'foodbanks_helped': foodbanks_helped,
            
            # Status breakdown
            'pending_donations': pending_donations,
            'accepted_donations': accepted_donations,
            'declined_donations': declined_donations,
            
            # Discussions
            'total_discussions': total_discussions,
            'active_discussions': active_discussions,
            
            # Charts data
            'monthly_data': list(monthly_data),
            'foodbank_data': list(foodbank_data),
            'type_breakdown': list(type_breakdown),
        }
        
    elif user_type == 'FOODBANK':
        from authentication.models import DonationAllocation, DonationDiscussion
        
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
        
        # All donations received (lifetime)
        all_donations = Donation.objects.filter(foodbank=foodbank_profile)
        
        # Period donations
        period_donations = all_donations.filter(
            donated_at__date__gte=start_dt,
            donated_at__date__lte=end_dt
        )
        
        # Lifetime statistics
        lifetime_donations = all_donations.count()
        lifetime_money = all_donations.filter(donation_type='money').aggregate(
            total=Sum('amount'))['total'] or 0
        lifetime_subsidized = all_donations.filter(donation_type='subsidized').aggregate(
            total=Sum('amount'))['total'] or 0
        lifetime_donors = all_donations.values('donor').distinct().count()
        
        # Period statistics
        total_donations_received = period_donations.count()
        total_amount_received = period_donations.filter(donation_type='money').aggregate(
            total=Sum('amount'))['total'] or 0
        total_items_received = period_donations.filter(donation_type='item').count()
        total_subsidized_received = period_donations.filter(donation_type='subsidized').count()
        unique_donors = period_donations.values('donor').distinct().count()
        
        # Request statistics
        all_requests = FoodBankRequest.objects.filter(foodbank=foodbank_profile)
        total_requests = all_requests.count()
        active_requests = all_requests.filter(status='active').count()
        fulfilled_requests = all_requests.filter(status='fulfilled').count()
        urgent_requests = all_requests.filter(priority='urgent', status='active').count()
        
        # Allocation statistics
        total_allocations = DonationAllocation.objects.filter(
            donation__foodbank=foodbank_profile
        ).count()
        pending_acknowledgments = DonationAllocation.objects.filter(
            donation__foodbank=foodbank_profile,
            is_acknowledged=False
        ).count()
        
        # Discussion statistics
        total_discussions = DonationDiscussion.objects.filter(foodbank=foodbank_profile).count()
        active_discussions = DonationDiscussion.objects.filter(
            foodbank=foodbank_profile, status='in_progress'
        ).count()
        
        # Monthly breakdown
        monthly_data = period_donations.annotate(
            month=TruncMonth('donated_at')
        ).values('month').annotate(
            count=Count('id'),
            amount=Sum('amount')
        ).order_by('month')
        
        # Top donors
        top_donors = all_donations.values(
            'donor__email', 'donor__donor_profile__full_name'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-count')[:10]
        
        # Donation type breakdown
        type_breakdown = period_donations.values('donation_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        context = {
            'user_type': user_type,
            'start_date': start_date,
            'end_date': end_date,
            
            # Lifetime stats
            'lifetime_donations': lifetime_donations,
            'lifetime_money': float(lifetime_money),
            'lifetime_subsidized': float(lifetime_subsidized),
            'lifetime_total_value': float(lifetime_money + lifetime_subsidized),
            'lifetime_donors': lifetime_donors,
            
            # Period stats
            'total_donations_received': total_donations_received,
            'total_amount_received': float(total_amount_received),
            'total_items_received': total_items_received,
            'total_subsidized_received': total_subsidized_received,
            'unique_donors': unique_donors,
            
            # Request stats
            'total_requests': total_requests,
            'active_requests': active_requests,
            'fulfilled_requests': fulfilled_requests,
            'urgent_requests': urgent_requests,
            
            # Allocation stats
            'total_allocations': total_allocations,
            'pending_acknowledgments': pending_acknowledgments,
            
            # Discussion stats
            'total_discussions': total_discussions,
            'active_discussions': active_discussions,
            
            # Charts data
            'monthly_data': list(monthly_data),
            'top_donors': list(top_donors),
            'type_breakdown': list(type_breakdown),
        }
    
    elif user_type == 'RECIPIENT':
        from authentication.models import RequestManagement, UnspecifiedDonationManagement
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
        
        # Get only completed requests that have been confirmed as received
        completed_requests_list = RequestManagement.objects.filter(
            recipient=recipient_profile,
            status='fulfilled',
            acknowledged_by_recipient=True,
            additional_notes__icontains='Receipt Confirmed',
            time_of_request__date__gte=start_dt,
            time_of_request__date__lte=end_dt
        ).select_related(
            'foodbank', 'assigned_foodbank'
        ).order_by('-time_of_request')
        
        # Get completed unspecified donations (accepted by recipient and received)
        completed_unspecified_list = UnspecifiedDonationManagement.objects.filter(
            accepted_by_recipient=recipient_profile,
            recipient_status='received',
            created_at__date__gte=start_dt,
            created_at__date__lte=end_dt
        ).select_related(
            'donation', 'donation__donor', 'donation__foodbank'
        ).order_by('-created_at')
        
        # Get completed subsidized donations (accepted by recipient and received)
        completed_subsidized_list = Donation.objects.filter(
            donation_type='subsidized',
            accepted_by_recipient=recipient_profile,
            delivery_status='delivered',
            donated_at__date__gte=start_dt,
            donated_at__date__lte=end_dt
        ).select_related(
            'donor', 'foodbank'
        ).order_by('-donated_at')
        
        # Calculate summary statistics
        total_completed = completed_requests_list.count()
        total_quantity = completed_requests_list.aggregate(total=Sum('quantity'))['total'] or 0
        total_unspecified = completed_unspecified_list.count()
        total_subsidized = completed_subsidized_list.count()
        
        # Pagination for completed requests
        requests_page = request.GET.get('requests_page', 1)
        requests_paginator = Paginator(completed_requests_list, 10)
        try:
            completed_requests = requests_paginator.page(requests_page)
        except PageNotAnInteger:
            completed_requests = requests_paginator.page(1)
        except EmptyPage:
            completed_requests = requests_paginator.page(requests_paginator.num_pages)
        
        # Pagination for unspecified donations
        unspecified_page = request.GET.get('unspecified_page', 1)
        unspecified_paginator = Paginator(completed_unspecified_list, 10)
        try:
            completed_unspecified = unspecified_paginator.page(unspecified_page)
        except PageNotAnInteger:
            completed_unspecified = unspecified_paginator.page(1)
        except EmptyPage:
            completed_unspecified = unspecified_paginator.page(unspecified_paginator.num_pages)
        
        # Pagination for subsidized donations
        subsidized_page = request.GET.get('subsidized_page', 1)
        subsidized_paginator = Paginator(completed_subsidized_list, 10)
        try:
            completed_subsidized = subsidized_paginator.page(subsidized_page)
        except PageNotAnInteger:
            completed_subsidized = subsidized_paginator.page(1)
        except EmptyPage:
            completed_subsidized = subsidized_paginator.page(subsidized_paginator.num_pages)
        
        context = {
            'user_type': user_type,
            'start_date': start_date,
            'end_date': end_date,
            'completed_requests': completed_requests,
            'total_completed': total_completed,
            'total_quantity': total_quantity,
            'completed_unspecified': completed_unspecified,
            'total_unspecified': total_unspecified,
            'completed_subsidized': completed_subsidized,
            'total_subsidized': total_subsidized,
        }
        
    else:  # ADMIN
        total_users = CustomUser.objects.count()
        total_donations = Donation.objects.count()
        total_amount = Donation.objects.filter(donation_type='money').aggregate(
            total=Sum('amount'))['total'] or 0
        total_foodbanks = FoodBankProfile.objects.count()
        
        context = {
            'user_type': user_type,
            'total_users': total_users,
            'total_donations': total_donations,
            'total_amount': float(total_amount),
            'total_foodbanks': total_foodbanks,
        }
    
    # Route to appropriate template based on user type
    if user_type == 'RECIPIENT':
        return render(request, 'reports/recipient_comprehensive_report.html', context)
    elif user_type == 'FOODBANK':
        return render(request, 'reports/foodbank_comprehensive_report.html', context)
    elif user_type == 'DONOR':
        return render(request, 'reports/donor_comprehensive_report.html', context)
    else:
        return render(request, 'reports/reports_dashboard.html', context)


@login_required
def donor_donation_history(request):
    """Detailed donation history report for donors"""
    if request.user.user_type != 'DONOR':
        return redirect('reports_dashboard')
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 6 months if no dates provided
    if not start_date:
        start_date = (timezone.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    # Convert to datetime objects
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get donations in date range
    donations = Donation.objects.filter(
        donor=request.user,
        donated_at__date__gte=start_dt,
        donated_at__date__lte=end_dt
    ).select_related('foodbank', 'foodbank_request').order_by('-donated_at')
    
    # Calculate summary statistics
    total_donations = donations.count()
    total_amount = donations.filter(donation_type='money').aggregate(
        total=Sum('amount'))['total'] or 0
    total_items = donations.filter(donation_type='item').count()
    total_subsidized = donations.filter(donation_type='subsidized').count()
    
    # Monthly breakdown
    monthly_data = donations.extra(
        select={'month': "DATE_TRUNC('month', donated_at)"}
    ).values('month').annotate(
        count=Count('id'),
        amount=Sum('amount')
    ).order_by('month')
    
    # Food bank breakdown
    foodbank_data = donations.values('foodbank__foodbank_name').annotate(
        count=Count('id'),
        amount=Sum('amount')
    ).order_by('-count')
    
    context = {
        'donations': donations,
        'start_date': start_date,
        'end_date': end_date,
        'total_donations': total_donations,
        'total_amount': float(total_amount),
        'total_items': total_items,
        'total_subsidized': total_subsidized,
        'monthly_data': monthly_data,
        'foodbank_data': foodbank_data,
    }
    
    return render(request, 'reports/donor_donation_history.html', context)


@login_required
def donor_impact_report(request):
    """Impact summary report for donors with sustainability metrics"""
    if request.user.user_type != 'DONOR':
        return redirect('reports_dashboard')
    
    # Get all donations
    donations = Donation.objects.filter(donor=request.user)
    
    # Calculate basic impact metrics
    total_donations = donations.count()
    total_amount = donations.filter(donation_type='money').aggregate(
        total=Sum('amount'))['total'] or 0
    total_items = donations.filter(donation_type='item').aggregate(
        total=Sum('quantity'))['total'] or 0
    total_subsidized = donations.filter(donation_type='subsidized').aggregate(
        total=Sum('subsidized_quantity'))['total'] or 0
    
    # Estimate impact
    lives_impacted = total_donations * 3  # Estimate 3 people per donation
    meals_provided = total_items + total_subsidized
    communities_helped = donations.values('foodbank').distinct().count()
    
    # Urgent response metrics
    urgent_donations = donations.filter(foodbank_request__priority__in=['urgent', 'high']).count()
    
    # === NEW SUSTAINABILITY METRICS ===
    
    # 1. Food Waste Prevented (kg)
    food_waste_prevented_kg = 0
    
    # Calculate from food donations (items)
    food_donations = donations.filter(
        donation_type='item',
        donation_category='food'
    )
    
    for donation in food_donations:
        if donation.quantity and donation.quantity_unit:
            # Convert to kg
            if donation.quantity_unit in ['kg', 'kilograms']:
                food_waste_prevented_kg += donation.quantity
            elif donation.quantity_unit in ['tons']:
                food_waste_prevented_kg += donation.quantity * 1000
            elif donation.quantity_unit in ['grams']:
                food_waste_prevented_kg += donation.quantity / 1000
            elif donation.quantity_unit in ['bags', 'packets']:
                food_waste_prevented_kg += donation.quantity * 5  # Assume 5kg per bag
            elif donation.quantity_unit in ['items', 'pieces']:
                food_waste_prevented_kg += donation.quantity * 0.5  # Assume 0.5kg per item
    
    # Add subsidized food donations
    subsidized_food = donations.filter(
        donation_type='subsidized',
        donation_category='food'
    )
    
    for donation in subsidized_food:
        if donation.subsidized_quantity and donation.subsidized_quantity_unit:
            if donation.subsidized_quantity_unit in ['kg', 'kilograms']:
                food_waste_prevented_kg += donation.subsidized_quantity
            elif donation.subsidized_quantity_unit in ['tons']:
                food_waste_prevented_kg += donation.subsidized_quantity * 1000
            elif donation.subsidized_quantity_unit in ['grams']:
                food_waste_prevented_kg += donation.subsidized_quantity / 1000
            elif donation.subsidized_quantity_unit in ['bags', 'packets']:
                food_waste_prevented_kg += donation.subsidized_quantity * 5
            elif donation.subsidized_quantity_unit in ['items', 'pieces']:
                food_waste_prevented_kg += donation.subsidized_quantity * 0.5
    
    # 2. CO₂ Saved (tons) - 1 kg of food waste = 2.5 kg CO₂ equivalent
    co2_saved_kg = food_waste_prevented_kg * 2.5
    co2_saved_tons = co2_saved_kg / 1000
    
    # 3. Non-Food Resource Impact
    non_food_donations = donations.filter(
        donation_category='non_food'
    )
    
    # Calculate waste reduction from non-food items
    non_food_waste_reduced_kg = 0
    non_food_co2_saved_kg = 0
    
    for donation in non_food_donations:
        if donation.donation_type == 'item' and donation.quantity:
            # Estimate based on typical non-food items (clothing, hygiene products, etc.)
            if donation.quantity_unit in ['kg', 'kilograms']:
                non_food_waste_reduced_kg += donation.quantity
                non_food_co2_saved_kg += donation.quantity * 3.5  # Non-food items have higher carbon footprint
            elif donation.quantity_unit in ['items', 'pieces']:
                non_food_waste_reduced_kg += donation.quantity * 0.3  # Assume 0.3kg per item
                non_food_co2_saved_kg += donation.quantity * 0.3 * 3.5
            elif donation.quantity_unit in ['bags', 'boxes']:
                non_food_waste_reduced_kg += donation.quantity * 3  # Assume 3kg per bag/box
                non_food_co2_saved_kg += donation.quantity * 3 * 3.5
    
    # 4. Monetary and CSR Contributions
    # Calculate total monetary value of all donations
    total_monetary_value = float(total_amount)
    
    # Add value of subsidized goods (market price)
    subsidized_market_value = donations.filter(
        donation_type='subsidized'
    ).aggregate(total=Sum('subsidized_market_price'))['total'] or 0
    total_monetary_value += float(subsidized_market_value)
    
    # Calculate CSR impact
    csr_donations = donations.filter(donation_type='csr')
    csr_count = csr_donations.count()
    
    # Assign sustainability value equivalents
    csr_impact_score = 0
    for donation in csr_donations:
        if donation.csr_subcategory == 'environmental':
            csr_impact_score += 100  # High environmental impact
        elif donation.csr_subcategory == 'humanitarian':
            csr_impact_score += 80
        elif donation.csr_subcategory == 'philanthropy':
            csr_impact_score += 70
        elif donation.csr_subcategory == 'volunteerism':
            csr_impact_score += 60
        else:
            csr_impact_score += 50
    
    # Calculate total environmental impact (combined CO2 saved)
    total_co2_saved_tons = (co2_saved_kg + non_food_co2_saved_kg) / 1000
    total_waste_prevented_kg = food_waste_prevented_kg + non_food_waste_reduced_kg
    
    # Monthly trends (last 12 months)
    twelve_months_ago = timezone.now() - timedelta(days=365)
    monthly_trends = donations.filter(
        donated_at__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('donated_at')
    ).values('month').annotate(
        count=Count('id'),
        amount=Sum('amount')
    ).order_by('month')
    
    # Donation type breakdown for charts
    donation_type_breakdown = donations.values('donation_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Category breakdown
    category_breakdown = donations.values('donation_category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Top food banks supported
    top_foodbanks = donations.values(
        'foodbank__foodbank_name', 'foodbank__contact_person'
    ).annotate(
        donation_count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-donation_count')[:5]
    
    # Prepare data for charts (JSON serializable)
    monthly_trends_data = {
        'labels': [trend['month'].strftime('%b %Y') for trend in monthly_trends],
        'donations': [trend['count'] for trend in monthly_trends],
        'amounts': [float(trend['amount'] or 0) for trend in monthly_trends]
    }
    
    donation_type_data = {
        'labels': [item['donation_type'].title() for item in donation_type_breakdown],
        'values': [item['count'] for item in donation_type_breakdown]
    }
    
    category_data = {
        'labels': [item['donation_category'].replace('_', ' ').title() for item in category_breakdown],
        'values': [item['count'] for item in category_breakdown]
    }
    
    context = {
        # Basic metrics
        'total_donations': total_donations,
        'total_amount': float(total_amount),
        'total_items': total_items,
        'total_subsidized': total_subsidized,
        'lives_impacted': lives_impacted,
        'meals_provided': meals_provided,
        'communities_helped': communities_helped,
        'urgent_donations': urgent_donations,
        
        # Sustainability metrics
        'food_waste_prevented_kg': round(food_waste_prevented_kg, 2),
        'co2_saved_tons': round(total_co2_saved_tons, 2),
        'non_food_waste_reduced_kg': round(non_food_waste_reduced_kg, 2),
        'total_waste_prevented_kg': round(total_waste_prevented_kg, 2),
        'total_monetary_value': round(total_monetary_value, 2),
        'csr_donations_count': csr_count,
        'csr_impact_score': csr_impact_score,
        
        # Chart data
        'monthly_trends': monthly_trends,
        'monthly_trends_json': json.dumps(monthly_trends_data),
        'donation_type_json': json.dumps(donation_type_data),
        'category_json': json.dumps(category_data),
        'top_foodbanks': top_foodbanks,
    }
    
    return render(request, 'reports/donor_impact_report.html', context)


@login_required
def foodbank_donations_received(request):
    """Donations received report for food banks"""
    if request.user.user_type != 'FOODBANK':
        return redirect('reports_dashboard')
    
    foodbank_profile = request.user.foodbank_profile
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 6 months if no dates provided
    if not start_date:
        start_date = (timezone.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    # Convert to datetime objects
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get donations received in date range
    donations = Donation.objects.filter(
        foodbank=foodbank_profile,
        donated_at__date__gte=start_dt,
        donated_at__date__lte=end_dt
    ).select_related('donor', 'donor__donor_profile', 'foodbank_request').order_by('-donated_at')
    
    # Calculate summary statistics
    total_donations = donations.count()
    total_amount = donations.filter(donation_type='money').aggregate(
        total=Sum('amount'))['total'] or 0
    total_items = donations.filter(donation_type='item').aggregate(
        total=Sum('quantity'))['total'] or 0
    total_subsidized = donations.filter(donation_type='subsidized').aggregate(
        total=Sum('subsidized_quantity'))['total'] or 0
    
    # Donor breakdown
    donor_data = donations.values(
        'donor__donor_profile__full_name', 'donor__email'
    ).annotate(
        donation_count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-donation_count')
    
    # Monthly breakdown
    monthly_data = donations.extra(
        select={'month': "DATE_TRUNC('month', donated_at)"}
    ).values('month').annotate(
        count=Count('id'),
        amount=Sum('amount')
    ).order_by('month')
    
    # Request fulfillment data
    request_fulfillment = donations.filter(
        foodbank_request__isnull=False
    ).values('foodbank_request__title', 'foodbank_request__priority').annotate(
        donation_count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-donation_count')
    
    context = {
        'donations': donations,
        'start_date': start_date,
        'end_date': end_date,
        'total_donations': total_donations,
        'total_amount': float(total_amount),
        'total_items': total_items,
        'total_subsidized': total_subsidized,
        'donor_data': donor_data,
        'monthly_data': monthly_data,
        'request_fulfillment': request_fulfillment,
    }
    
    return render(request, 'reports/foodbank_donations_received.html', context)


@login_required
def foodbank_request_fulfillment(request):
    """Request fulfillment report for food banks"""
    if request.user.user_type != 'FOODBANK':
        return redirect('reports_dashboard')
    
    foodbank_profile = request.user.foodbank_profile
    
    # Get all requests
    requests = FoodBankRequest.objects.filter(foodbank=foodbank_profile).order_by('-created_at')
    
    # Calculate fulfillment statistics
    total_requests = requests.count()
    fulfilled_requests = requests.filter(status='fulfilled').count()
    active_requests = requests.filter(status='active').count()
    expired_requests = requests.filter(status='expired').count()
    
    fulfillment_rate = (fulfilled_requests / total_requests * 100) if total_requests > 0 else 0
    
    # Priority breakdown
    priority_data = requests.values('priority').annotate(
        total=Count('id'),
        fulfilled=Count('id', filter=Q(status='fulfilled')),
        active=Count('id', filter=Q(status='active')),
        expired=Count('id', filter=Q(status='expired'))
    ).order_by('priority')
    
    # Response time analysis
    fulfilled_with_donations = requests.filter(
        status='fulfilled',
        donations__isnull=False
    ).annotate(
        response_time=F('donations__donated_at') - F('created_at')
    ).values('id', 'title', 'priority', 'response_time')
    
    # Monthly request trends
    monthly_requests = requests.extra(
        select={'month': "DATE_TRUNC('month', created_at)"}
    ).values('month').annotate(
        total=Count('id'),
        fulfilled=Count('id', filter=Q(status='fulfilled'))
    ).order_by('month')
    
    context = {
        'requests': requests,
        'total_requests': total_requests,
        'fulfilled_requests': fulfilled_requests,
        'active_requests': active_requests,
        'expired_requests': expired_requests,
        'fulfillment_rate': fulfillment_rate,
        'priority_data': priority_data,
        'fulfilled_with_donations': fulfilled_with_donations,
        'monthly_requests': monthly_requests,
    }
    
    return render(request, 'reports/foodbank_request_fulfillment.html', context)


@login_required
def admin_platform_analytics(request):
    """Platform analytics report for admins"""
    if request.user.user_type != 'ADMIN':
        return redirect('reports_dashboard')
    
    # User statistics
    total_users = CustomUser.objects.count()
    total_donors = CustomUser.objects.filter(user_type='DONOR').count()
    total_foodbanks = CustomUser.objects.filter(user_type='FOODBANK').count()
    total_recipients = CustomUser.objects.filter(user_type='RECIPIENT').count()
    
    # Donation statistics
    total_donations = Donation.objects.count()
    total_amount = Donation.objects.filter(donation_type='money').aggregate(
        total=Sum('amount'))['total'] or 0
    total_items = Donation.objects.filter(donation_type='item').aggregate(
        total=Sum('quantity'))['total'] or 0
    
    # Request statistics
    total_requests = FoodBankRequest.objects.count()
    fulfilled_requests = FoodBankRequest.objects.filter(status='fulfilled').count()
    active_requests = FoodBankRequest.objects.filter(status='active').count()
    
    # User growth over time (last 12 months)
    twelve_months_ago = timezone.now() - timedelta(days=365)
    user_growth = CustomUser.objects.filter(
        date_joined__gte=twelve_months_ago
    ).extra(
        select={'month': "DATE_TRUNC('month', date_joined)"}
    ).values('month', 'user_type').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Donation trends
    donation_trends = Donation.objects.filter(
        donated_at__gte=twelve_months_ago
    ).extra(
        select={'month': "DATE_TRUNC('month', donated_at)"}
    ).values('month').annotate(
        count=Count('id'),
        amount=Sum('amount')
    ).order_by('month')
    
    # Top performing food banks
    top_foodbanks = FoodBankProfile.objects.annotate(
        donation_count=Count('donation'),
        total_amount=Sum('donation__amount')
    ).order_by('-donation_count')[:10]
    
    # Payment processing statistics
    payment_stats = PaymentTransaction.objects.aggregate(
        total_transactions=Count('id'),
        completed_transactions=Count('id', filter=Q(status='completed')),
        failed_transactions=Count('id', filter=Q(status='failed')),
        total_amount=Sum('amount'),
        total_fees=Sum('transaction_fee')
    )
    
    context = {
        'total_users': total_users,
        'total_donors': total_donors,
        'total_foodbanks': total_foodbanks,
        'total_recipients': total_recipients,
        'total_donations': total_donations,
        'total_amount': float(total_amount),
        'total_items': total_items,
        'total_requests': total_requests,
        'fulfilled_requests': fulfilled_requests,
        'active_requests': active_requests,
        'user_growth': user_growth,
        'donation_trends': donation_trends,
        'top_foodbanks': top_foodbanks,
        'payment_stats': payment_stats,
    }
    
    return render(request, 'reports/admin_platform_analytics.html', context)


def export_donor_donation_history_csv(request):
    """Export donor donation history as CSV"""
    if request.user.user_type != 'DONOR':
        return redirect('reports_dashboard')
    
    # Get date range from request
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
        donor=request.user,
        donated_at__date__gte=start_dt,
        donated_at__date__lte=end_dt
    ).select_related('foodbank', 'foodbank_request').order_by('-donated_at')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="donation_history_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Type', 'Food Bank', 'Item/Description', 'Quantity', 'Amount (KES)', 
        'Request Title', 'Priority', 'Status', 'Message'
    ])
    
    for donation in donations:
        writer.writerow([
            donation.donated_at.strftime('%Y-%m-%d %H:%M'),
            donation.get_donation_type_display(),
            donation.foodbank.foodbank_name,
            donation.item_name or donation.subsidized_product_type or 'N/A',
            donation.quantity or donation.subsidized_quantity or 'N/A',
            donation.amount or donation.subsidized_price or 'N/A',
            donation.foodbank_request.title if donation.foodbank_request else 'General Donation',
            donation.foodbank_request.priority if donation.foodbank_request else 'N/A',
            donation.foodbank_request.status if donation.foodbank_request else 'N/A',
            donation.message or 'N/A'
        ])
    
    return response


def export_donor_impact_pdf(request):
    """Export donor impact report as PDF with sustainability metrics"""
    if request.user.user_type != 'DONOR':
        return redirect('reports_dashboard')
    
    # Get donor data
    donations = Donation.objects.filter(donor=request.user)
    donor_profile = request.user.donor_profile
    
    # Calculate basic metrics
    total_donations = donations.count()
    total_amount = donations.filter(donation_type='money').aggregate(
        total=Sum('amount'))['total'] or 0
    lives_impacted = total_donations * 3
    communities_helped = donations.values('foodbank').distinct().count()
    
    # Calculate sustainability metrics (same logic as in donor_impact_report view)
    food_waste_prevented_kg = 0
    food_donations = donations.filter(donation_type='item', donation_category='food')
    for donation in food_donations:
        if donation.quantity and donation.quantity_unit:
            if donation.quantity_unit in ['kg', 'kilograms']:
                food_waste_prevented_kg += donation.quantity
            elif donation.quantity_unit in ['tons']:
                food_waste_prevented_kg += donation.quantity * 1000
            elif donation.quantity_unit in ['grams']:
                food_waste_prevented_kg += donation.quantity / 1000
            elif donation.quantity_unit in ['bags', 'packets']:
                food_waste_prevented_kg += donation.quantity * 5
            elif donation.quantity_unit in ['items', 'pieces']:
                food_waste_prevented_kg += donation.quantity * 0.5
    
    subsidized_food = donations.filter(donation_type='subsidized', donation_category='food')
    for donation in subsidized_food:
        if donation.subsidized_quantity and donation.subsidized_quantity_unit:
            if donation.subsidized_quantity_unit in ['kg', 'kilograms']:
                food_waste_prevented_kg += donation.subsidized_quantity
            elif donation.subsidized_quantity_unit in ['tons']:
                food_waste_prevented_kg += donation.subsidized_quantity * 1000
            elif donation.subsidized_quantity_unit in ['grams']:
                food_waste_prevented_kg += donation.subsidized_quantity / 1000
            elif donation.subsidized_quantity_unit in ['bags', 'packets']:
                food_waste_prevented_kg += donation.subsidized_quantity * 5
            elif donation.subsidized_quantity_unit in ['items', 'pieces']:
                food_waste_prevented_kg += donation.subsidized_quantity * 0.5
    
    co2_saved_tons = (food_waste_prevented_kg * 2.5) / 1000
    
    non_food_donations = donations.filter(donation_category='non_food')
    non_food_waste_reduced_kg = 0
    for donation in non_food_donations:
        if donation.donation_type == 'item' and donation.quantity:
            if donation.quantity_unit in ['kg', 'kilograms']:
                non_food_waste_reduced_kg += donation.quantity
            elif donation.quantity_unit in ['items', 'pieces']:
                non_food_waste_reduced_kg += donation.quantity * 0.3
            elif donation.quantity_unit in ['bags', 'boxes']:
                non_food_waste_reduced_kg += donation.quantity * 3
    
    total_waste_prevented_kg = food_waste_prevented_kg + non_food_waste_reduced_kg
    
    subsidized_market_value = donations.filter(donation_type='subsidized').aggregate(
        total=Sum('subsidized_market_price'))['total'] or 0
    total_monetary_value = float(total_amount) + float(subsidized_market_value)
    
    csr_count = donations.filter(donation_type='csr').count()
    
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
        alignment=1  # Center
    )
    story.append(Paragraph("Sustainability Impact Report", title_style))
    story.append(Spacer(1, 20))
    
    # Donor info
    story.append(Paragraph(f"<b>Donor:</b> {donor_profile.full_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Email:</b> {request.user.email}", styles['Normal']))
    story.append(Paragraph(f"<b>Report Date:</b> {timezone.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Basic Impact Summary
    story.append(Paragraph("Basic Impact Metrics", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Donations', str(total_donations)],
        ['Total Amount (KES)', f"{total_amount:,.2f}"],
        ['Lives Impacted', str(lives_impacted)],
        ['Communities Helped', str(communities_helped)],
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
    
    # Sustainability Metrics
    story.append(Paragraph("Environmental Impact", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    sustainability_data = [
        ['Metric', 'Value'],
        ['Food Waste Prevented (kg)', f"{food_waste_prevented_kg:,.2f}"],
        ['CO₂ Saved (tons)', f"{co2_saved_tons:,.2f}"],
        ['Non-Food Waste Reduced (kg)', f"{non_food_waste_reduced_kg:,.2f}"],
        ['Total Waste Prevented (kg)', f"{total_waste_prevented_kg:,.2f}"],
    ]
    
    sustainability_table = Table(sustainability_data)
    sustainability_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(sustainability_table)
    story.append(Spacer(1, 30))
    
    # CSR & Monetary Impact
    story.append(Paragraph("CSR & Financial Contributions", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    csr_data = [
        ['Metric', 'Value'],
        ['Total Monetary Value (KES)', f"{total_monetary_value:,.2f}"],
        ['CSR Initiatives', str(csr_count)],
    ]
    
    csr_table = Table(csr_data)
    csr_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(csr_table)
    story.append(Spacer(1, 30))
    
    # Recent donations
    story.append(Paragraph("Recent Donations", styles['Heading2']))
    recent_donations = donations.order_by('-donated_at')[:10]
    
    if recent_donations:
        donation_data = [['Date', 'Type', 'Food Bank', 'Amount/Quantity']]
        for donation in recent_donations:
            amount_qty = str(donation.amount) if donation.amount else f"{donation.quantity} {donation.quantity_unit}"
            donation_data.append([
                donation.donated_at.strftime('%Y-%m-%d'),
                donation.get_donation_type_display(),
                donation.foodbank.foodbank_name,
                amount_qty
            ])
        
        donation_table = Table(donation_data)
        donation_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(donation_table)
    else:
        story.append(Paragraph("No donations found.", styles['Normal']))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="impact_report_{request.user.email}_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response


def export_donor_donation_history_pdf(request):
    """Export donor donation history as PDF"""
    if request.user.user_type != 'DONOR':
        return redirect('reports_dashboard')
    
    # Get date range from request
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
        donor=request.user,
        donated_at__date__gte=start_dt,
        donated_at__date__lte=end_dt
    ).select_related('foodbank', 'foodbank_request').order_by('-donated_at')
    
    # Calculate summary
    total_donations = donations.count()
    total_amount = donations.filter(donation_type='money').aggregate(
        total=Sum('amount'))['total'] or 0
    total_items = donations.filter(donation_type='item').count()
    total_subsidized = donations.filter(donation_type='subsidized').count()
    
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
    story.append(Paragraph("Donation History Report", title_style))
    story.append(Spacer(1, 20))
    
    # Report info
    story.append(Paragraph(f"<b>Donor:</b> {request.user.donor_profile.full_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Email:</b> {request.user.email}", styles['Normal']))
    story.append(Paragraph(f"<b>Period:</b> {start_date} to {end_date}", styles['Normal']))
    story.append(Paragraph(f"<b>Report Date:</b> {timezone.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Total Donations', str(total_donations)],
        ['Total Amount (KES)', f"{total_amount:,.2f}"],
        ['Item Donations', str(total_items)],
        ['Subsidized Goods', str(total_subsidized)],
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
    
    # Donations table
    story.append(Paragraph("Donation Details", styles['Heading2']))
    
    if donations:
        donation_data = [['Date', 'Type', 'Food Bank', 'Item/Description', 'Quantity', 'Amount (KES)']]
        for donation in donations:
            item_desc = donation.item_name or donation.subsidized_product_type or 'N/A'
            quantity = f"{donation.quantity} {donation.quantity_unit}" if donation.quantity else f"{donation.subsidized_quantity} {donation.subsidized_quantity_unit}" if donation.subsidized_quantity else 'N/A'
            amount = f"{donation.amount:,.2f}" if donation.amount else f"{donation.subsidized_price:,.2f}" if donation.subsidized_price else 'N/A'
            
            donation_data.append([
                donation.donated_at.strftime('%Y-%m-%d'),
                donation.get_donation_type_display(),
                donation.foodbank.foodbank_name,
                item_desc,
                quantity,
                amount
            ])
        
        donation_table = Table(donation_data)
        donation_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(donation_table)
    else:
        story.append(Paragraph("No donations found for the selected period.", styles['Normal']))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="donation_history_{start_date}_to_{end_date}.pdf"'
    
    return response


def export_foodbank_donations_received_pdf(request):
    """Export foodbank donations received as PDF"""
    if request.user.user_type != 'FOODBANK':
        return redirect('reports_dashboard')
    
    foodbank_profile = request.user.foodbank_profile
    
    # Get date range from request
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
    
    # Calculate summary
    total_donations = donations.count()
    total_amount = donations.filter(donation_type='money').aggregate(
        total=Sum('amount'))['total'] or 0
    total_items = donations.filter(donation_type='item').aggregate(
        total=Sum('quantity'))['total'] or 0
    total_subsidized = donations.filter(donation_type='subsidized').aggregate(
        total=Sum('subsidized_quantity'))['total'] or 0
    
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
    story.append(Paragraph("Donations Received Report", title_style))
    story.append(Spacer(1, 20))
    
    # Food bank info
    story.append(Paragraph(f"<b>Food Bank:</b> {foodbank_profile.foodbank_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Contact Person:</b> {foodbank_profile.contact_person}", styles['Normal']))
    story.append(Paragraph(f"<b>Period:</b> {start_date} to {end_date}", styles['Normal']))
    story.append(Paragraph(f"<b>Report Date:</b> {timezone.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Total Donations Received', str(total_donations)],
        ['Total Amount (KES)', f"{total_amount:,.2f}"],
        ['Total Items Received', str(total_items)],
        ['Total Subsidized Goods', str(total_subsidized)],
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
    
    # Donations table
    story.append(Paragraph("Donation Details", styles['Heading2']))
    
    if donations:
        donation_data = [['Date', 'Donor', 'Type', 'Item/Description', 'Quantity', 'Amount (KES)']]
        for donation in donations:
            donor_name = donation.donor.donor_profile.full_name if hasattr(donation.donor, 'donor_profile') else donation.donor.email
            item_desc = donation.item_name or donation.subsidized_product_type or 'N/A'
            quantity = f"{donation.quantity} {donation.quantity_unit}" if donation.quantity else f"{donation.subsidized_quantity} {donation.subsidized_quantity_unit}" if donation.subsidized_quantity else 'N/A'
            amount = f"{donation.amount:,.2f}" if donation.amount else f"{donation.subsidized_price:,.2f}" if donation.subsidized_price else 'N/A'
            
            donation_data.append([
                donation.donated_at.strftime('%Y-%m-%d'),
                donor_name,
                donation.get_donation_type_display(),
                item_desc,
                quantity,
                amount
            ])
        
        donation_table = Table(donation_data)
        donation_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(donation_table)
    else:
        story.append(Paragraph("No donations received for the selected period.", styles['Normal']))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="donations_received_{start_date}_to_{end_date}.pdf"'
    
    return response


def export_foodbank_request_fulfillment_pdf(request):
    """Export foodbank request fulfillment as PDF"""
    if request.user.user_type != 'FOODBANK':
        return redirect('reports_dashboard')
    
    foodbank_profile = request.user.foodbank_profile
    
    # Get all requests
    requests = FoodBankRequest.objects.filter(foodbank=foodbank_profile).order_by('-created_at')
    
    # Calculate fulfillment statistics
    total_requests = requests.count()
    fulfilled_requests = requests.filter(status='fulfilled').count()
    active_requests = requests.filter(status='active').count()
    expired_requests = requests.filter(status='expired').count()
    fulfillment_rate = (fulfilled_requests / total_requests * 100) if total_requests > 0 else 0
    
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
    story.append(Paragraph("Request Fulfillment Report", title_style))
    story.append(Spacer(1, 20))
    
    # Food bank info
    story.append(Paragraph(f"<b>Food Bank:</b> {foodbank_profile.foodbank_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Contact Person:</b> {foodbank_profile.contact_person}", styles['Normal']))
    story.append(Paragraph(f"<b>Report Date:</b> {timezone.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Total Requests', str(total_requests)],
        ['Fulfilled Requests', str(fulfilled_requests)],
        ['Active Requests', str(active_requests)],
        ['Expired Requests', str(expired_requests)],
        ['Fulfillment Rate', f"{fulfillment_rate:.1f}%"],
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
        request_data = [['Date', 'Title', 'Priority', 'Status', 'Quantity Needed', 'Donations Received']]
        for req in requests:
            donations_received = req.donations.count()
            request_data.append([
                req.created_at.strftime('%Y-%m-%d'),
                req.title[:30] + '...' if len(req.title) > 30 else req.title,
                req.get_priority_display(),
                req.get_status_display(),
                f"{req.quantity_needed} {req.quantity_unit}" if req.quantity_needed else 'N/A',
                str(donations_received)
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
        story.append(Paragraph("No requests found.", styles['Normal']))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response["Content-Disposition"] = f"attachment; filename=\"request_fulfillment_{timezone.now().strftime('%Y%m%d')}.pdf\""
    
    return response


def export_admin_platform_analytics_pdf(request):
    """Export admin platform analytics as PDF"""
    if request.user.user_type != 'ADMIN':
        return redirect('reports_dashboard')
    
    # Get platform statistics
    total_users = CustomUser.objects.count()
    total_donors = CustomUser.objects.filter(user_type='DONOR').count()
    total_foodbanks = CustomUser.objects.filter(user_type='FOODBANK').count()
    total_recipients = CustomUser.objects.filter(user_type='RECIPIENT').count()
    total_donations = Donation.objects.count()
    total_amount = Donation.objects.filter(donation_type='money').aggregate(
        total=Sum('amount'))['total'] or 0
    total_requests = FoodBankRequest.objects.count()
    fulfilled_requests = FoodBankRequest.objects.filter(status='fulfilled').count()
    
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
    story.append(Paragraph("Platform Analytics Report", title_style))
    story.append(Spacer(1, 20))
    
    # Report info
    story.append(Paragraph(f"<b>Report Date:</b> {timezone.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Paragraph(f"<b>Generated By:</b> {request.user.email}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # User statistics
    story.append(Paragraph("User Statistics", styles['Heading2']))
    user_data = [
        ['User Type', 'Count'],
        ['Total Users', str(total_users)],
        ['Donors', str(total_donors)],
        ['Food Banks', str(total_foodbanks)],
        ['Recipients', str(total_recipients)],
    ]
    
    user_table = Table(user_data)
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(user_table)
    story.append(Spacer(1, 20))
    
    # Platform statistics
    story.append(Paragraph("Platform Statistics", styles['Heading2']))
    platform_data = [
        ['Metric', 'Value'],
        ['Total Donations', str(total_donations)],
        ['Total Amount (KES)', f"{total_amount:,.2f}"],
        ['Total Requests', str(total_requests)],
        ['Fulfilled Requests', str(fulfilled_requests)],
        ['Fulfillment Rate', f"{(fulfilled_requests / total_requests * 100):.1f}%" if total_requests > 0 else "0%"],
    ]
    
    platform_table = Table(platform_data)
    platform_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(platform_table)
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response["Content-Disposition"] = f"attachment; filename=\"platform_analytics_{timezone.now().strftime('%Y%m%d')}.pdf\""
    
    return response
