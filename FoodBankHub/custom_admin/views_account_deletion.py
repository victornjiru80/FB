"""
Account Deletion Management Views for Custom Admin Panel
Handles user account deletion requests with approval workflow
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .decorators import staff_member_required
from django.db.models import Q, Count, Sum
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse

from authentication.models import (
    AccountDeletionRequest, CustomUser, Notification,
    Donation, FoodBankRequest, RecipientRequest, DonationAllocation
)


@staff_member_required
def account_deletion_requests(request):
    """
    Main view for managing account deletion requests
    Shows all requests with filtering and bulk actions
    """
    # Get filter parameters
    status_filter = request.GET.get('status', 'pending')
    user_type_filter = request.GET.get('user_type', '')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    sort_by = request.GET.get('sort', '-requested_at')
    
    # Base queryset
    requests_qs = AccountDeletionRequest.objects.select_related(
        'user', 'processed_by'
    ).all()
    
    # Apply filters
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    
    if user_type_filter:
        requests_qs = requests_qs.filter(user__user_type=user_type_filter)
    
    if search:
        requests_qs = requests_qs.filter(
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(admin_notes__icontains=search)
        )
    
    if date_from:
        requests_qs = requests_qs.filter(requested_at__gte=date_from)
    
    if date_to:
        requests_qs = requests_qs.filter(requested_at__lte=date_to)
    
    # Sorting
    requests_qs = requests_qs.order_by(sort_by)
    
    # Statistics
    total_requests = AccountDeletionRequest.objects.count()
    pending_requests = AccountDeletionRequest.objects.filter(status='pending').count()
    approved_requests = AccountDeletionRequest.objects.filter(status='approved').count()
    rejected_requests = AccountDeletionRequest.objects.filter(status='rejected').count()
    
    # Requests by user type
    requests_by_type = AccountDeletionRequest.objects.values(
        'user__user_type'
    ).annotate(count=Count('id'))
    
    # Pagination
    paginator = Paginator(requests_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Account Deletion Requests',
        'page_obj': page_obj,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'requests_by_type': requests_by_type,
        'status_choices': AccountDeletionRequest.STATUS_CHOICES,
        'user_types': ['DONOR', 'FOODBANK', 'RECIPIENT'],
        'current_filters': {
            'status': status_filter,
            'user_type': user_type_filter,
            'search': search,
            'date_from': date_from,
            'date_to': date_to,
            'sort': sort_by,
        }
    }
    
    return render(request, 'custom_admin/account_deletion_requests.html', context)


@staff_member_required
def account_deletion_detail(request, request_id):
    """
    Detailed view of a single account deletion request
    Shows user information and related data
    """
    deletion_request = get_object_or_404(
        AccountDeletionRequest.objects.select_related('user', 'processed_by'),
        id=request_id
    )
    
    user = deletion_request.user
    
    # Get user-related data to show impact of deletion
    user_data = {
        'donations_count': 0,
        'requests_count': 0,
        'allocations_count': 0,
        'profile_type': user.user_type,
    }
    
    if user.user_type == 'DONOR':
        user_data['donations_count'] = Donation.objects.filter(donor=user).count()
        user_data['total_donated'] = Donation.objects.filter(
            donor=user, donation_type='money'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    elif user.user_type == 'FOODBANK':
        user_data['requests_count'] = FoodBankRequest.objects.filter(
            foodbank=user.foodbank_profile
        ).count()
        user_data['donations_received'] = Donation.objects.filter(
            foodbank=user.foodbank_profile
        ).count()
    
    elif user.user_type == 'RECIPIENT':
        user_data['requests_count'] = RecipientRequest.objects.filter(
            recipient=user.recipient_profile
        ).count()
        user_data['allocations_count'] = DonationAllocation.objects.filter(
            recipient=user.recipient_profile
        ).count()
    
    context = {
        'title': f'Deletion Request - {user.email}',
        'deletion_request': deletion_request,
        'user_data': user_data,
    }
    
    return render(request, 'custom_admin/account_deletion_detail.html', context)


@staff_member_required
def approve_deletion_request(request, request_id):
    """
    Approve an account deletion request
    Deactivates the user account and marks request as approved
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('custom_admin:account_deletion_requests')
    
    deletion_request = get_object_or_404(AccountDeletionRequest, id=request_id)
    
    if deletion_request.status != 'pending':
        messages.warning(request, 'This request has already been processed.')
        return redirect('custom_admin:account_deletion_detail', request_id=request_id)
    
    # Get admin notes if provided
    admin_notes = request.POST.get('admin_notes', '')
    
    # Deactivate user
    user = deletion_request.user
    user.is_active = False
    user.save()
    
    # Update deletion request
    deletion_request.status = 'approved'
    deletion_request.processed_by = request.user
    deletion_request.processed_at = timezone.now()
    deletion_request.admin_notes = admin_notes
    deletion_request.save()
    
    # Notify user
    Notification.objects.create(
        user=user,
        notification_type='system',
        message=f"Your account deletion request has been approved. Your account has been deactivated. {admin_notes}"
    )
    
    messages.success(request, f'Account deletion request for {user.email} has been approved.')
    return redirect('custom_admin:account_deletion_requests')


@staff_member_required
def reject_deletion_request(request, request_id):
    """
    Reject an account deletion request
    User account remains active
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('custom_admin:account_deletion_requests')
    
    deletion_request = get_object_or_404(AccountDeletionRequest, id=request_id)
    
    if deletion_request.status != 'pending':
        messages.warning(request, 'This request has already been processed.')
        return redirect('custom_admin:account_deletion_detail', request_id=request_id)
    
    # Get admin notes (required for rejection)
    admin_notes = request.POST.get('admin_notes', '')
    
    if not admin_notes:
        messages.error(request, 'Please provide a reason for rejection.')
        return redirect('custom_admin:account_deletion_detail', request_id=request_id)
    
    # Update deletion request
    deletion_request.status = 'rejected'
    deletion_request.processed_by = request.user
    deletion_request.processed_at = timezone.now()
    deletion_request.admin_notes = admin_notes
    deletion_request.save()
    
    # Notify user
    Notification.objects.create(
        user=deletion_request.user,
        notification_type='system',
        message=f"Your account deletion request has been rejected. Reason: {admin_notes}"
    )

    # Email user the rejection reason
    try:
        subject = 'Account Deletion Request Rejected - FoodBank Hub'
        message = (
            f"Hello {deletion_request.user.email},\n\n"
            "Your account deletion request has been reviewed and rejected.\n\n"
            f"Reason provided by the administrator:\n{admin_notes}\n\n"
            "If you believe this was a mistake or you need help, please contact support.\n\n"
            "Regards,\nFoodBank Hub Team\n"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[deletion_request.user.email],
            fail_silently=True,
        )
    except Exception:
        pass
    
    messages.success(request, f'Account deletion request for {deletion_request.user.email} has been rejected.')
    return redirect('custom_admin:account_deletion_requests')


@staff_member_required
def bulk_process_deletion_requests(request):
    """
    Bulk approve or reject deletion requests
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    action = request.POST.get('action')
    request_ids = request.POST.getlist('request_ids[]')
    
    if not action or not request_ids:
        return JsonResponse({'error': 'Missing action or request IDs'}, status=400)
    
    requests_qs = AccountDeletionRequest.objects.filter(
        id__in=request_ids,
        status='pending'
    )
    
    processed_count = 0
    
    if action == 'approve':
        for deletion_request in requests_qs:
            user = deletion_request.user
            user.is_active = False
            user.save()
            
            deletion_request.status = 'approved'
            deletion_request.processed_by = request.user
            deletion_request.processed_at = timezone.now()
            deletion_request.save()
            
            Notification.objects.create(
                user=user,
                notification_type='system',
                message="Your account deletion request has been approved. Your account has been deactivated."
            )
            
            processed_count += 1
    
    elif action == 'reject':
        admin_notes = request.POST.get('bulk_notes', 'Rejected by administrator')
        
        for deletion_request in requests_qs:
            deletion_request.status = 'rejected'
            deletion_request.processed_by = request.user
            deletion_request.processed_at = timezone.now()
            deletion_request.admin_notes = admin_notes
            deletion_request.save()
            
            Notification.objects.create(
                user=deletion_request.user,
                notification_type='system',
                message=f"Your account deletion request has been rejected. Reason: {admin_notes}"
            )
            
            processed_count += 1
    
    return JsonResponse({
        'success': True,
        'processed_count': processed_count,
        'message': f'{processed_count} request(s) {action}d successfully.'
    })


@staff_member_required
def deletion_requests_stats(request):
    """
    API endpoint for deletion requests statistics
    Used for dashboard widgets
    """
    stats = {
        'total': AccountDeletionRequest.objects.count(),
        'pending': AccountDeletionRequest.objects.filter(status='pending').count(),
        'approved': AccountDeletionRequest.objects.filter(status='approved').count(),
        'rejected': AccountDeletionRequest.objects.filter(status='rejected').count(),
        'by_user_type': {}
    }
    
    # Count by user type
    for user_type in ['DONOR', 'FOODBANK', 'RECIPIENT']:
        stats['by_user_type'][user_type] = AccountDeletionRequest.objects.filter(
            user__user_type=user_type
        ).count()
    
    return JsonResponse(stats)
