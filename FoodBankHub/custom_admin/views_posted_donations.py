from django.shortcuts import render, get_object_or_404
from .decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.urls import reverse
from authentication.models import Donation, DonorProfile, UnspecifiedDonationManagement, FoodBankProfile, DonationResponse


@staff_member_required
def posted_donations_management(request):
    """
    Manage posted donations (completed donations).
    Shows all donations that have been delivered successfully.
    """
    # Get filter parameters
    search = request.GET.get('search', '')
    donation_type = request.GET.get('donation_type', '')
    donation_category = request.GET.get('donation_category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    sort_by = request.GET.get('sort_by', 'newest')
    
    # Base queryset - completed donations
    donations = Donation.objects.filter(
        status='accepted',
        delivery_status='delivered'
    ).select_related(
        'donor',
        'donor__donor_profile',
        'foodbank',
        'foodbank__user',
        'foodbank_request',
        'foodbank_request__original_request',
        'foodbank_request__original_request__recipient',
        'foodbank_request__original_request__foodbank'
    ).prefetch_related(
        'allocations__recipient__user'
    )  # Removed slice to avoid ordering conflict
    
    # Apply search filter
    if search:
        donations = donations.filter(
            Q(donor__email__icontains=search) |
            Q(donor__donor_profile__full_name__icontains=search) |
            Q(donor__donor_profile__organization_name__icontains=search) |
            Q(foodbank__foodbank_name__icontains=search) |
            Q(item_name__icontains=search) |
            Q(message__icontains=search)
        )
    
    # Apply donation type filter
    if donation_type:
        donations = donations.filter(donation_type=donation_type)
    
    # Apply donation category filter
    if donation_category:
        donations = donations.filter(donation_category=donation_category)
    
    # Apply date range filters
    if date_from:
        parsed_from = parse_date(date_from)
        if parsed_from:
            donations = donations.filter(donated_at__date__gte=parsed_from)
    if date_to:
        parsed_to = parse_date(date_to)
        if parsed_to:
            donations = donations.filter(donated_at__date__lte=parsed_to)
    
    # Apply sorting
    if sort_by == 'oldest':
        donations = donations.order_by('donated_at')
    elif sort_by == 'amount_high':
        donations = donations.order_by('-amount')
    elif sort_by == 'amount_low':
        donations = donations.order_by('amount')
    else:  # newest (default)
        donations = donations.order_by('-donated_at')
    
    # Pagination
    paginator = Paginator(donations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_count = donations.count()
    total_monetary = donations.filter(donation_type='money').count()
    total_items = donations.filter(donation_type='item').count()
    total_subsidized = donations.filter(donation_type='subsidized').count()
    
    context = {
        'title': 'Posted Donations',
        'page_obj': page_obj,
        'search': search,
        'donation_type': donation_type,
        'donation_category': donation_category,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
        'reset_url': reverse('custom_admin:posted_donations_management'),
        'total_count': total_count,
        'total_monetary': total_monetary,
        'total_items': total_items,
        'total_subsidized': total_subsidized,
        'donation_types': Donation.DONATION_TYPES,
        'donation_categories': Donation.DONATION_CATEGORIES,
    }
    
    return render(request, 'custom_admin/posted_donations_management.html', context)


@staff_member_required
def posted_unspecified_donations(request):
    """Manage posted unspecified donations (completed = received by recipient)."""
    foodbank_filter = request.GET.get('foodbank') or ''
    date_from = request.GET.get('date_from') or ''
    date_to = request.GET.get('date_to') or ''
    search = (request.GET.get('search') or '').strip()
    donation_type_filter = request.GET.get('donation_type') or ''
    category_filter = request.GET.get('category') or ''
    delivery_filter = request.GET.get('delivery') or ''

    donations = UnspecifiedDonationManagement.objects.select_related(
        'donation__donor',
        'donation__foodbank',
        'accepted_by_recipient'
    ).filter(
        recipient_status='received'
    ).order_by('-created_at')

    if foodbank_filter:
        donations = donations.filter(donation__foodbank_id=foodbank_filter)
    if date_from:
        parsed_from = parse_date(date_from)
        if parsed_from:
            donations = donations.filter(created_at__date__gte=parsed_from)
    if date_to:
        parsed_to = parse_date(date_to)
        if parsed_to:
            donations = donations.filter(created_at__date__lte=parsed_to)
    if search:
        donations = donations.filter(
            Q(donation__donor__email__icontains=search) |
            Q(donation__donor__donor_profile__full_name__icontains=search) |
            Q(donation__donor__donor_profile__organization_name__icontains=search) |
            Q(donation__foodbank__foodbank_name__icontains=search) |
            Q(donation__item_name__icontains=search) |
            Q(donation__message__icontains=search)
        )
    if donation_type_filter:
        donations = donations.filter(donation__donation_type=donation_type_filter)
    if category_filter:
        donations = donations.filter(donation__donation_category=category_filter)
    if delivery_filter:
        donations = donations.filter(donation__delivery_method=delivery_filter)

    total_donations = donations.count()
    pending_foodbank = 0
    accepted_by_foodbank = 0
    declined_by_foodbank = 0
    pending_recipient = 0
    accepted_by_recipient = 0
    received = total_donations

    paginator = Paginator(donations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    foodbanks = FoodBankProfile.objects.filter(is_approved='approved', user__is_active=True).order_by('foodbank_name')

    get_copy = request.GET.copy()
    get_copy.pop('page', None)
    pagination_query_string = get_copy.urlencode()

    context = {
        'title': 'Posted Unspecified Donations',
        'posted_view': True,
        'page_obj': page_obj,
        'total_donations': total_donations,
        'pending_foodbank': pending_foodbank,
        'accepted_by_foodbank': accepted_by_foodbank,
        'declined_by_foodbank': declined_by_foodbank,
        'pending_recipient': pending_recipient,
        'accepted_by_recipient': accepted_by_recipient,
        'received': received,
        'foodbanks': foodbanks,
        'donation_type_choices': Donation.DONATION_TYPES,
        'category_choices': Donation.DONATION_CATEGORIES,
        'delivery_choices': Donation.DELIVERY_METHODS,
        'pagination_query_string': pagination_query_string,
        'clear_url': reverse('custom_admin:posted_unspecified_donations'),
        'current_filters': {
            'foodbank_status': '',
            'recipient_status': 'received',
            'foodbank': foodbank_filter,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
            'donation_type': donation_type_filter,
            'category': category_filter,
            'delivery': delivery_filter,
        }
    }
    return render(request, 'custom_admin/unspecified_donations_management.html', context)


@staff_member_required
def posted_subsidized_donations(request):
    """Manage posted subsidized donations (completed = accepted + delivered).
    Uses the same template as manage view for consistent columns."""
    foodbank_filter = request.GET.get('foodbank')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    category_filter = request.GET.get('category')
    delivery_filter = request.GET.get('delivery')
    recipient_claimed_filter = request.GET.get('recipient_claimed')
    has_responses = request.GET.get('has_responses', '')

    donations = Donation.objects.filter(
        donation_type='subsidized',
        status='accepted',
        delivery_status='delivered',
    ).select_related(
        'donor', 'donor__donor_profile', 'foodbank', 'accepted_by_recipient',
    ).prefetch_related('subsidized_responded_by').order_by('-donated_at')

    if search:
        donations = donations.filter(
            Q(donor__email__icontains=search) |
            Q(donor__donor_profile__full_name__icontains=search) |
            Q(donor__donor_profile__organization_name__icontains=search) |
            Q(foodbank__foodbank_name__icontains=search) |
            Q(subsidized_product_type__icontains=search) |
            Q(message__icontains=search)
        )
    if foodbank_filter:
        donations = donations.filter(foodbank_id=foodbank_filter)
    if date_from:
        parsed_from = parse_date(date_from)
        if parsed_from:
            donations = donations.filter(donated_at__date__gte=parsed_from)
    if date_to:
        parsed_to = parse_date(date_to)
        if parsed_to:
            donations = donations.filter(donated_at__date__lte=parsed_to)
    if category_filter:
        donations = donations.filter(donation_category=category_filter)
    if delivery_filter:
        donations = donations.filter(delivery_method=delivery_filter)
    if recipient_claimed_filter == 'yes':
        donations = donations.filter(accepted_by_recipient__isnull=False)
    elif recipient_claimed_filter == 'no':
        donations = donations.filter(accepted_by_recipient__isnull=True)
    if has_responses == 'yes':
        donations = donations.filter(subsidized_responded_by__isnull=False).distinct()
    elif has_responses == 'no':
        donations = donations.filter(subsidized_responded_by__isnull=True)

    total_count = donations.count()

    paginator = Paginator(donations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    foodbanks = FoodBankProfile.objects.filter(is_approved='approved', user__is_active=True).order_by('foodbank_name')

    donation_list = list(page_obj.object_list)
    if donation_list:
        donation_ids = [donation.id for donation in donation_list]
        recipient_notes = (
            DonationResponse.objects.filter(donation_id__in=donation_ids)
            .exclude(notes__isnull=True)
            .exclude(notes__exact='')
            .order_by('-responded_at')
        )

        latest_notes = {}
        for response in recipient_notes:
            if response.donation_id not in latest_notes:
                latest_notes[response.donation_id] = response.notes

        for donation in donation_list:
            donation.latest_recipient_note = latest_notes.get(donation.id)

    get_copy = request.GET.copy()
    get_copy.pop('page', None)
    pagination_query_string = get_copy.urlencode()

    recipient_claimed_choices = [
        ('', 'All'),
        ('yes', 'Claimed by recipient'),
        ('no', 'Not claimed'),
    ]

    context = {
        'title': 'Posted Subsidized Donations',
        'posted_view': True,
        'clear_url': reverse('custom_admin:posted_subsidized_donations'),
        'page_obj': page_obj,
        'total_donations': total_count,
        'pending': 0,
        'accepted': total_count,
        'declined': 0,
        'total_value': sum(d.subsidized_price or 0 for d in page_obj.object_list),
        'foodbanks': foodbanks,
        'category_choices': Donation.DONATION_CATEGORIES,
        'delivery_choices': Donation.DELIVERY_METHODS,
        'recipient_claimed_choices': recipient_claimed_choices,
        'pagination_query_string': pagination_query_string,
        'current_filters': {
            'status': 'accepted',
            'foodbank': foodbank_filter,
            'has_responses': has_responses,
            'search': search,
            'date_from': date_from,
            'date_to': date_to,
            'category': category_filter,
            'delivery': delivery_filter,
            'recipient_claimed': recipient_claimed_filter,
        }
    }

    return render(request, 'custom_admin/subsidized_donations_management.html', context)


@staff_member_required
def posted_specified_donations(request):
    """Manage posted specified donations (completed = fulfilled requests).
    Uses the same template as manage view for consistent columns."""
    from authentication.models import RequestManagement

    status_filter = request.GET.get('status', '')
    foodbank_filter = request.GET.get('foodbank')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    request_type_filter = request.GET.get('request_type')
    request_category_filter = request.GET.get('request_category')
    delivery_filter = request.GET.get('delivery')
    donation_type_filter = request.GET.get('donation_type')

    # Show fulfilled / acknowledged requests
    request_qs = RequestManagement.objects.filter(
        status__in=['fulfilled', 'acknowledged']
    ).select_related(
        'recipient', 'foodbank', 'assigned_foodbank',
        'donation', 'donation__donor__donor_profile',
        'foodbank_request',
    ).prefetch_related(
        'foodbank_request_created__donations',
        'foodbank_request_created__donations__donor__donor_profile',
        'donor_requests__donations',
        'donor_requests__donations__donor__donor_profile',
    ).order_by('-time_of_request')

    if status_filter:
        request_qs = request_qs.filter(status=status_filter)
    if foodbank_filter:
        request_qs = request_qs.filter(
            Q(foodbank_id=foodbank_filter) | Q(assigned_foodbank_id=foodbank_filter)
        )
    if search:
        request_qs = request_qs.filter(
            Q(description__icontains=search) |
            Q(recipient__full_name__icontains=search) |
            Q(recipient__user__email__icontains=search) |
            Q(location__icontains=search) |
            Q(additional_notes__icontains=search)
        )
    if date_from:
        parsed_from = parse_date(date_from)
        if parsed_from:
            request_qs = request_qs.filter(time_of_request__date__gte=parsed_from)
    if date_to:
        parsed_to = parse_date(date_to)
        if parsed_to:
            request_qs = request_qs.filter(time_of_request__date__lte=parsed_to)
    if request_type_filter:
        request_qs = request_qs.filter(request_type=request_type_filter)
    if request_category_filter:
        request_qs = request_qs.filter(request_category=request_category_filter)
    if delivery_filter:
        request_qs = request_qs.filter(delivery_method=delivery_filter)
    if donation_type_filter:
        request_qs = request_qs.filter(
            foodbank_request_created__donations__donation_type=donation_type_filter
        ).distinct()

    # Statistics
    total_requests = request_qs.count()

    paginator = Paginator(request_qs, 15)
    request_page = request.GET.get('requests_page')
    request_page_obj = paginator.get_page(request_page)

    # Attach linked data and status metadata (matching manage view logic)
    def _admin_status_meta(req_obj):
        base_text = req_obj.get_display_status() if hasattr(req_obj, 'get_display_status') else req_obj.get_status_display()
        meta = {'text': base_text, 'bg': '#dcfce7', 'color': '#166534', 'icon': 'fas fa-check-circle'}
        if req_obj.status == 'acknowledged':
            meta.update(text='Recipient Acknowledged', bg='#dcfce7', color='#15803d', icon='fas fa-check-double')
        return meta

    from .views_donations import _resolve_specified_links
    for req in request_page_obj.object_list:
        fb_request, linked_donation = _resolve_specified_links(req)
        req.linked_foodbank_request = fb_request
        req.linked_donation = linked_donation
        status_meta = _admin_status_meta(req)
        req.admin_status_text = status_meta['text']
        req.admin_status_bg = status_meta['bg']
        req.admin_status_color = status_meta['color']
        req.admin_status_icon = status_meta['icon']

    foodbanks = FoodBankProfile.objects.filter(is_approved='approved', user__is_active=True).order_by('foodbank_name')

    get_copy = request.GET.copy()
    get_copy.pop('requests_page', None)
    pagination_query_string = get_copy.urlencode()

    context = {
        'title': 'Posted Specified Donations',
        'posted_view': True,
        'clear_url': reverse('custom_admin:posted_specified_donations'),
        'request_page_obj': request_page_obj,
        'total_requests': total_requests,
        'request_pending': 0,
        'request_partial': 0,
        'request_fulfilled': total_requests,
        'request_declined': 0,
        'total_donations': 0,
        'pending': 0,
        'accepted': 0,
        'declined': 0,
        'total_monetary': 0,
        'total_items': 0,
        'foodbanks': foodbanks,
        'status_choices': RequestManagement.STATUS_CHOICES if hasattr(RequestManagement, 'STATUS_CHOICES') else [],
        'request_type_choices': getattr(RequestManagement, 'REQUEST_TYPE_CHOICES', []),
        'request_category_choices': getattr(RequestManagement, 'REQUEST_CATEGORY_CHOICES', []),
        'delivery_choices': getattr(RequestManagement, 'DELIVERY_METHOD_CHOICES', []),
        'donation_type_choices': Donation.DONATION_TYPES,
        'pagination_query_string': pagination_query_string,
        'current_filters': {
            'status': status_filter,
            'foodbank': foodbank_filter,
            'search': search,
            'date_from': date_from,
            'date_to': date_to,
            'request_type': request_type_filter,
            'request_category': request_category_filter,
            'delivery': delivery_filter,
            'donation_type': donation_type_filter,
        }
    }

    return render(request, 'custom_admin/specified_donations_management.html', context)


@staff_member_required
def posted_donation_detail(request, donation_id):
    """View detailed information about a posted donation"""
    donation = get_object_or_404(
        Donation.objects.select_related(
            'donor',
            'donor__donor_profile',
            'foodbank',
            'foodbank__user'
        ).prefetch_related(
            'allocations__recipient__user'
        ),
        id=donation_id,
        delivery_status='delivered',
        status='accepted'
    )
    
    # Get donor profile information
    donor_profile = None
    if hasattr(donation.donor, 'donor_profile'):
        donor_profile = donation.donor.donor_profile
    
    context = {
        'title': f'Posted Donation #{donation.id}',
        'donation': donation,
        'donor_profile': donor_profile,
    }
    
    return render(request, 'custom_admin/posted_donation_detail.html', context)
