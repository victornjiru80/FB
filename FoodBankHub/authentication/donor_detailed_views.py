from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .models import Donation, DonationResponse, UnspecifiedDonationManagement, FoodBankProfile
from .decorators import donor_required


def _apply_donor_subsidized_status_filter(queryset, status_filter):
    """Apply donor subsidized status filtering using table-visible status values."""
    status_key = (status_filter or '').strip().lower()
    if not status_key or status_key == 'all':
        return queryset

    if status_key in ('pending', 'awaiting_foodbank'):
        return queryset.filter(status='pending')
    if status_key in ('declined', 'declined_by_foodbank'):
        return queryset.filter(status='declined')
    if status_key in ('fulfilled', 'fulfilled_allocated'):
        return queryset.filter(status='fulfilled')
    if status_key == 'accepted_by_recipient':
        return queryset.filter(accepted_by_recipient__isnull=False)
    if status_key == 'rejected_by_recipient_broadcasted':
        return queryset.filter(
            status='accepted',
            declined_by_recipient__isnull=False,
            accepted_by_recipient__isnull=True,
        )
    if status_key in ('accepted', 'accepted_by_foodbank'):
        return queryset.filter(
            status='accepted',
            accepted_by_recipient__isnull=True,
            declined_by_recipient__isnull=True,
        )

    # Unknown status key should not hide records unexpectedly.
    return queryset


def _build_unspecified_effective_note_maps(items):
    """
    Build effective recipient note/decline note maps for donor unspecified table.
    If a donation is later accepted/received, prior recipient decline notes must be hidden.
    """
    item_list = list(items)
    donation_ids = [item.donation_id for item in item_list if getattr(item, 'donation_id', None)]
    if not donation_ids:
        return {}, {}

    latest_non_decline_notes_by_donation = {}
    latest_declines_by_donation = {}
    accepted_notes_by_donation = {}
    accepted_recipient_by_donation = {
        item.donation_id: item.accepted_by_recipient_id
        for item in item_list
        if getattr(item, 'accepted_by_recipient_id', None)
    }

    responses = DonationResponse.objects.filter(
        donation_id__in=donation_ids
    ).exclude(
        notes__isnull=True
    ).exclude(
        notes__exact=''
    ).select_related('recipient').order_by('-responded_at')

    for response in responses:
        donation_id = response.donation_id

        if response.response_type == 'declined':
            if donation_id not in latest_declines_by_donation:
                latest_declines_by_donation[donation_id] = response.notes
        elif donation_id not in latest_non_decline_notes_by_donation:
            latest_non_decline_notes_by_donation[donation_id] = response.notes

        if (
            response.response_type == 'accepted'
            and accepted_recipient_by_donation.get(donation_id) == response.recipient_id
            and donation_id not in accepted_notes_by_donation
        ):
            accepted_notes_by_donation[donation_id] = response.notes

    effective_recipient_notes = {}
    effective_recipient_declines = {}

    for item in item_list:
        donation_id = item.donation_id
        base_recipient_note = (getattr(item, 'recipient_notes', None) or '').strip()
        base_decline_note = (getattr(item, 'recipient_decline_reason', None) or '').strip()
        accepted_or_received = bool(getattr(item, 'accepted_by_recipient_id', None)) or getattr(item, 'recipient_status', None) in (
            'accepted_by_recipient', 'received'
        )

        if accepted_or_received:
            effective_recipient_notes[item.id] = (
                accepted_notes_by_donation.get(donation_id)
                or base_recipient_note
                or ''
            )
            effective_recipient_declines[item.id] = ''
        else:
            effective_recipient_notes[item.id] = (
                latest_non_decline_notes_by_donation.get(donation_id)
                or base_recipient_note
                or ''
            )
            effective_recipient_declines[item.id] = (
                base_decline_note
                or latest_declines_by_donation.get(donation_id)
                or ''
            )

    return effective_recipient_notes, effective_recipient_declines


@login_required
@donor_required
def donor_unspecified_donations_detail(request):
    """Comprehensive view for donor's unspecified donations with filters"""
    # Get all unspecified donations for this donor
    unspecified_donations = UnspecifiedDonationManagement.objects.filter(
        donation__donor=request.user
    ).select_related(
        'donation', 'donation__foodbank', 'accepted_by_recipient'
    ).order_by('-created_at')
    
    # Get filter parameters (aligned with table columns shown to donor)
    type_filter = request.GET.get('type', 'all')
    category_filter = request.GET.get('category', 'all')
    foodbank_location_filter = request.GET.get('foodbank_location', '').strip()
    foodbank_status_filter = request.GET.get('foodbank_status', 'all')
    recipient_status_filter = request.GET.get('recipient_status', 'all')
    delivery_filter = request.GET.get('delivery', 'all')
    quantity_range = request.GET.get('quantity_range', 'all').strip()
    amount_range = request.GET.get('amount_range', 'all').strip()
    search_query = request.GET.get('search', '').strip()

    # Normalize delivery value for UI/backward compatibility.
    if delivery_filter == 'dropoff':
        delivery_filter = 'delivery'
    
    # Apply filters
    if type_filter != 'all':
        # "Type" filter maps to donation_category in this table.
        unspecified_donations = unspecified_donations.filter(donation__donation_category=type_filter)
    
    if category_filter != 'all':
        # "Category" filter maps to donation_type in this table.
        unspecified_donations = unspecified_donations.filter(donation__donation_type=category_filter)

    if foodbank_location_filter:
        unspecified_donations = unspecified_donations.filter(
            donation__foodbank__address__icontains=foodbank_location_filter
        )
    
    if foodbank_status_filter != 'all':
        unspecified_donations = unspecified_donations.filter(foodbank_status=foodbank_status_filter)
    
    if recipient_status_filter != 'all':
        unspecified_donations = unspecified_donations.filter(recipient_status=recipient_status_filter)
    
    if delivery_filter != 'all':
        if delivery_filter == 'delivery':
            unspecified_donations = unspecified_donations.filter(
                donation__delivery_method__in=['dropoff', 'delivery']
            )
        else:
            unspecified_donations = unspecified_donations.filter(donation__delivery_method=delivery_filter)

    quantity_range_map = {
        '1-100': (1, 100),
        '101-500': (101, 500),
        '501-1000': (501, 1000),
        '1001-5000': (1001, 5000),
        '5001_or_more': (5001, None),
    }
    qty_min, qty_max = quantity_range_map.get(quantity_range, (None, None))
    if qty_min is not None:
        unspecified_donations = unspecified_donations.filter(
            Q(donation__quantity__gte=qty_min) |
            Q(donation__subsidized_quantity__gte=qty_min)
        )
    if qty_max is not None:
        unspecified_donations = unspecified_donations.filter(
            Q(donation__quantity__lte=qty_max) |
            Q(donation__subsidized_quantity__lte=qty_max)
        )

    amount_range_map = {
        '1-10000': (1, 10000),
        '10001-50000': (10001, 50000),
        '50001-100000': (50001, 100000),
        '100001-500000': (100001, 500000),
        '500001_or_more': (500001, None),
    }
    amt_min, amt_max = amount_range_map.get(amount_range, (None, None))
    if amt_min is not None:
        unspecified_donations = unspecified_donations.filter(
            Q(donation__amount__gte=amt_min) |
            Q(donation__subsidized_price__gte=amt_min)
        )
    if amt_max is not None:
        unspecified_donations = unspecified_donations.filter(
            Q(donation__amount__lte=amt_max) |
            Q(donation__subsidized_price__lte=amt_max)
        )
    
    if search_query:
        unspecified_donations = unspecified_donations.filter(
            Q(donation__item_name__icontains=search_query) |
            Q(donation__subsidized_product_type__icontains=search_query) |
            Q(donation__csr_description__icontains=search_query) |
            Q(donation__other_description__icontains=search_query) |
            Q(donation__foodbank__foodbank_name__icontains=search_query) |
            Q(donation__message__icontains=search_query) |
            Q(recipient_notes__icontains=search_query) |
            Q(foodbank_decline_reason__icontains=search_query) |
            Q(recipient_decline_reason__icontains=search_query)
        )
    
    # Get statistics
    total_count = unspecified_donations.count()
    pending_foodbank_count = unspecified_donations.filter(foodbank_status='pending_foodbank').count()
    accepted_count = unspecified_donations.filter(foodbank_status='accepted_by_foodbank').count()
    declined_count = unspecified_donations.filter(foodbank_status='declined_by_foodbank').count()
    received_count = unspecified_donations.filter(recipient_status='received').count()
    
    # Pagination
    paginator = Paginator(unspecified_donations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    page_items = list(page_obj.object_list)
    if page_items:
        effective_recipient_notes, effective_recipient_declines = _build_unspecified_effective_note_maps(page_items)
        for item in page_items:
            item.effective_recipient_note = effective_recipient_notes.get(item.id, '')
            item.effective_recipient_decline_note = effective_recipient_declines.get(item.id, '')
        page_obj.object_list = page_items
    
    context = {
        'donations': page_obj,
        'total_count': total_count,
        'pending_foodbank_count': pending_foodbank_count,
        'accepted_count': accepted_count,
        'declined_count': declined_count,
        'received_count': received_count,
        'type_filter': type_filter,
        'category_filter': category_filter,
        'foodbank_location_filter': foodbank_location_filter,
        'foodbank_status_filter': foodbank_status_filter,
        'recipient_status_filter': recipient_status_filter,
        'delivery_filter': delivery_filter,
        'quantity_range': quantity_range,
        'amount_range': amount_range,
        'search_query': search_query,
    }
    
    return render(request, 'authentication/donor_unspecified_donations_detail.html', context)


@login_required
@donor_required
def donor_subsidized_donations_detail(request):
    """Comprehensive view for donor's subsidized donations with filters"""
    # Get all subsidized donations for this donor
    subsidized_donations = Donation.objects.filter(
        donor=request.user,
        donation_type='subsidized',
        foodbank_request__isnull=True  # Only donor-initiated (unspecified) subsidized donations
    ).select_related(
        'foodbank',
        'accepted_by_recipient',
        'unspecified_management'
    ).order_by('-donated_at')
    
    # Get filter parameters (aligned with table columns: Food Bank, Type, Status, Delivery, New Price, Date, Recipient, Search)
    foodbank_filter = request.GET.get('foodbank', 'all')
    type_filter = (request.GET.get('type') or request.GET.get('category') or 'all').strip().lower()
    if type_filter not in ('all', 'food', 'non_food'):
        type_filter = 'all'
    status_filter = request.GET.get('status', 'all')
    delivery_filter = (request.GET.get('delivery', request.GET.get('delivery_status', 'all')) or 'all').strip().lower()
    if delivery_filter == 'dropoff':
        delivery_filter = 'delivery'
    if delivery_filter not in ('all', 'pickup', 'delivery'):
        delivery_filter = 'all'
    date_filter = request.GET.get('date_range', 'all')
    quantity_filter = request.GET.get('quantity', 'all')
    amount_filter = request.GET.get('amount', request.GET.get('price', 'all'))
    recipient_filter = request.GET.get('recipient', 'all')
    search_query = request.GET.get('search', '').strip()
    
    # Apply filters
    if foodbank_filter != 'all':
        subsidized_donations = subsidized_donations.filter(foodbank__id=foodbank_filter)
    
    if type_filter != 'all':
        subsidized_donations = subsidized_donations.filter(donation_category=type_filter)
    
    subsidized_donations = _apply_donor_subsidized_status_filter(subsidized_donations, status_filter)
    
    if delivery_filter != 'all':
        if delivery_filter == 'delivery':
            subsidized_donations = subsidized_donations.filter(delivery_method__in=['delivery', 'dropoff'])
        else:
            subsidized_donations = subsidized_donations.filter(delivery_method='pickup')
    
    if recipient_filter == 'claimed':
        subsidized_donations = subsidized_donations.filter(accepted_by_recipient__isnull=False)
    elif recipient_filter == 'unclaimed':
        subsidized_donations = subsidized_donations.filter(accepted_by_recipient__isnull=True)
    
    if search_query:
        subsidized_donations = subsidized_donations.filter(
            Q(subsidized_product_type__icontains=search_query) |
            Q(foodbank__foodbank_name__icontains=search_query) |
            Q(foodbank__address__icontains=search_query) |
            Q(message__icontains=search_query) |
            Q(csr_description__icontains=search_query) |
            Q(other_description__icontains=search_query)
        )
    
    # Filter by date range
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    if date_filter == 'custom' and (date_from or date_to):
        if date_from:
            try:
                from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d')
                from_date = timezone.make_aware(from_date.replace(hour=0, minute=0, second=0, microsecond=0))
                subsidized_donations = subsidized_donations.filter(donated_at__gte=from_date)
            except ValueError:
                pass
        if date_to:
            try:
                to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d')
                to_date = timezone.make_aware(to_date.replace(hour=23, minute=59, second=59, microsecond=999999))
                subsidized_donations = subsidized_donations.filter(donated_at__lte=to_date)
            except ValueError:
                pass
    elif date_filter != 'all':
        now = timezone.now()
        if date_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            subsidized_donations = subsidized_donations.filter(donated_at__gte=start_date)
        elif date_filter == 'week':
            start_date = now - timedelta(days=7)
            subsidized_donations = subsidized_donations.filter(donated_at__gte=start_date)
        elif date_filter == 'month':
            start_date = now - timedelta(days=30)
            subsidized_donations = subsidized_donations.filter(donated_at__gte=start_date)
        elif date_filter == '3months':
            start_date = now - timedelta(days=90)
            subsidized_donations = subsidized_donations.filter(donated_at__gte=start_date)
    
    # Filter by quantity range
    if quantity_filter != 'all':
        if quantity_filter == 'small':
            subsidized_donations = subsidized_donations.filter(subsidized_quantity__lte=100)
        elif quantity_filter == 'medium':
            subsidized_donations = subsidized_donations.filter(subsidized_quantity__gt=100, subsidized_quantity__lte=500)
        elif quantity_filter == 'large':
            subsidized_donations = subsidized_donations.filter(subsidized_quantity__gt=500)

    # Filter by amount range (subsidized new price)
    if amount_filter != 'all':
        if amount_filter == 'small':
            subsidized_donations = subsidized_donations.filter(subsidized_price__lte=100)
        elif amount_filter == 'medium':
            subsidized_donations = subsidized_donations.filter(subsidized_price__gt=100, subsidized_price__lte=500)
        elif amount_filter == 'large':
            subsidized_donations = subsidized_donations.filter(subsidized_price__gt=500)
    
    # Get statistics
    total_count = subsidized_donations.count()
    pending_count = subsidized_donations.filter(status='pending').count()
    accepted_count = subsidized_donations.filter(status='accepted').count()
    declined_count = subsidized_donations.filter(status='declined').count()
    delivered_count = subsidized_donations.filter(delivery_status='delivered').count()
    
    # Get unique foodbanks for filter dropdown
    foodbanks = FoodBankProfile.objects.filter(
        id__in=subsidized_donations.values_list('foodbank_id', flat=True).distinct(),
        user__is_active=True
    )
    
    # Pagination
    paginator = Paginator(subsidized_donations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Build effective recipient notes/decline notes from responses.
    # For donations that are eventually accepted, keep only acceptance note and clear decline note.
    donation_list = list(page_obj.object_list)
    donation_ids = [donation.id for donation in donation_list]
    latest_notes_by_donation = {}
    latest_declines_by_donation = {}
    accepted_notes_by_donation = {}
    accepted_recipient_by_donation = {
        donation.id: donation.accepted_by_recipient_id
        for donation in donation_list
        if donation.accepted_by_recipient_id
    }

    if donation_ids:
        donation_responses = DonationResponse.objects.filter(
            donation_id__in=donation_ids
        ).exclude(
            notes__isnull=True
        ).exclude(
            notes__exact=''
        ).select_related('recipient').order_by('-responded_at')

        for response in donation_responses:
            donation_id = response.donation_id

            if donation_id not in latest_notes_by_donation:
                latest_notes_by_donation[donation_id] = response.notes

            if response.response_type == 'declined' and donation_id not in latest_declines_by_donation:
                latest_declines_by_donation[donation_id] = response.notes

            if (
                response.response_type == 'accepted'
                and accepted_recipient_by_donation.get(donation_id) == response.recipient_id
                and donation_id not in accepted_notes_by_donation
            ):
                accepted_notes_by_donation[donation_id] = response.notes

        for donation in donation_list:
            unspecified = getattr(donation, 'unspecified_management', None)
            unspecified_recipient_note = (getattr(unspecified, 'recipient_notes', None) or '').strip()
            unspecified_decline_note = (getattr(unspecified, 'recipient_decline_reason', None) or '').strip()

            if donation.accepted_by_recipient_id:
                effective_recipient_note = (
                    accepted_notes_by_donation.get(donation.id)
                    or unspecified_recipient_note
                    or ''
                )
                effective_recipient_decline_note = ''
            else:
                effective_recipient_note = (
                    latest_notes_by_donation.get(donation.id)
                    or unspecified_recipient_note
                    or ''
                )
                effective_recipient_decline_note = (
                    unspecified_decline_note
                    or latest_declines_by_donation.get(donation.id)
                    or ''
                )

            donation.latest_recipient_note = effective_recipient_note
            donation.effective_recipient_note = effective_recipient_note
            donation.effective_recipient_decline_note = effective_recipient_decline_note

        # Replace the paginator's object list so templates receive enriched donations
        page_obj.object_list = donation_list
    
    context = {
        'donations': page_obj,
        'total_count': total_count,
        'pending_count': pending_count,
        'accepted_count': accepted_count,
        'declined_count': declined_count,
        'delivered_count': delivered_count,
        'foodbanks': foodbanks,
        'foodbank_filter': foodbank_filter,
        'type_filter': type_filter,
        'category_filter': type_filter,
        'status_filter': status_filter,
        'delivery_filter': delivery_filter,
        'date_filter': date_filter,
        'date_from': date_from,
        'date_to': date_to,
        'quantity_filter': quantity_filter,
        'amount_filter': amount_filter,
        'recipient_filter': recipient_filter,
        'search_query': search_query,
    }
    
    return render(request, 'authentication/donor_subsidized_donations_detail.html', context)


@login_required
@donor_required
def donor_request_donations_detail(request):
    """Comprehensive view for donor's request-based donations with filters"""
    # Get all request-based donations for this donor
    request_donations = Donation.objects.filter(
        donor=request.user,
        foodbank_request__isnull=False
    ).select_related(
        'foodbank', 'foodbank_request', 'foodbank_request__original_request__recipient'
    ).prefetch_related('allocations__recipient').order_by('-donated_at')
    
    # Get filter parameters
    foodbank_filter = request.GET.get('foodbank', 'all')
    status_filter = request.GET.get('status', 'all')
    allocation_filter = request.GET.get('allocation', 'all')
    date_filter = request.GET.get('date_range', 'all')
    amount_filter = request.GET.get('amount', 'all')
    search_query = request.GET.get('search', '').strip()
    
    # Apply filters
    if foodbank_filter != 'all':
        request_donations = request_donations.filter(foodbank__id=foodbank_filter)
    
    if status_filter != 'all':
        request_donations = request_donations.filter(status=status_filter)
    
    if allocation_filter != 'all':
        if allocation_filter == 'allocated':
            request_donations = request_donations.filter(allocations__isnull=False).distinct()
        elif allocation_filter == 'pending':
            request_donations = request_donations.filter(allocations__isnull=True, status='accepted')
    
    if search_query:
        request_donations = request_donations.filter(
            Q(item_name__icontains=search_query) |
            Q(foodbank__foodbank_name__icontains=search_query) |
            Q(foodbank_request__title__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    # Filter by date range
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    if date_filter == 'custom' and (date_from or date_to):
        if date_from:
            try:
                from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d')
                from_date = timezone.make_aware(from_date.replace(hour=0, minute=0, second=0, microsecond=0))
                request_donations = request_donations.filter(donated_at__gte=from_date)
            except ValueError:
                pass
        if date_to:
            try:
                to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d')
                to_date = timezone.make_aware(to_date.replace(hour=23, minute=59, second=59, microsecond=999999))
                request_donations = request_donations.filter(donated_at__lte=to_date)
            except ValueError:
                pass
    elif date_filter != 'all':
        now = timezone.now()
        if date_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            request_donations = request_donations.filter(donated_at__gte=start_date)
        elif date_filter == 'week':
            start_date = now - timedelta(days=7)
            request_donations = request_donations.filter(donated_at__gte=start_date)
        elif date_filter == 'month':
            start_date = now - timedelta(days=30)
            request_donations = request_donations.filter(donated_at__gte=start_date)
        elif date_filter == '3months':
            start_date = now - timedelta(days=90)
            request_donations = request_donations.filter(donated_at__gte=start_date)
    
    # Filter by amount/quantity range
    if amount_filter != 'all':
        if amount_filter == 'small':
            request_donations = request_donations.filter(
                Q(donation_type='item', quantity__lte=50) |
                Q(donation_type='money', amount__lte=5000)
            )
        elif amount_filter == 'medium':
            request_donations = request_donations.filter(
                Q(donation_type='item', quantity__gt=50, quantity__lte=200) |
                Q(donation_type='money', amount__gt=5000, amount__lte=20000)
            )
        elif amount_filter == 'large':
            request_donations = request_donations.filter(
                Q(donation_type='item', quantity__gt=200) |
                Q(donation_type='money', amount__gt=20000)
            )
    
    # Get statistics
    total_count = request_donations.count()
    pending_count = request_donations.filter(status='pending').count()
    accepted_count = request_donations.filter(status='accepted').count()
    declined_count = request_donations.filter(status='declined').count()
    allocated_count = request_donations.filter(allocations__isnull=False).distinct().count()
    
    # Get unique foodbanks for filter dropdown
    foodbanks = FoodBankProfile.objects.filter(
        id__in=request_donations.values_list('foodbank_id', flat=True).distinct(),
        user__is_active=True
    )
    
    # Pagination
    paginator = Paginator(request_donations, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'donations': page_obj,
        'total_count': total_count,
        'pending_count': pending_count,
        'accepted_count': accepted_count,
        'declined_count': declined_count,
        'allocated_count': allocated_count,
        'foodbanks': foodbanks,
        'foodbank_filter': foodbank_filter,
        'status_filter': status_filter,
        'allocation_filter': allocation_filter,
        'date_filter': date_filter,
        'date_from': date_from,
        'date_to': date_to,
        'amount_filter': amount_filter,
        'search_query': search_query,
    }
    
    return render(request, 'authentication/donor_request_donations_detail.html', context)
