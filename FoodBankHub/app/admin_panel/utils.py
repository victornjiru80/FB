from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from authentication.models import CustomUser, Donation, FoodBankRequest
import json


def get_dashboard_stats():
    """Get dashboard statistics"""
    stats = {
        'total_users': CustomUser.objects.count(),
        'total_donors': CustomUser.objects.filter(user_type='DONOR').count(),
        'total_foodbanks': CustomUser.objects.filter(user_type='FOODBANK').count(),
        'total_recipients': CustomUser.objects.filter(user_type='RECIPIENT').count(),
        'total_donations': Donation.objects.count(),
        'total_donated_amount': Donation.objects.aggregate(
            total=Sum('amount'))['total'] or 0,
        'active_requests': FoodBankRequest.objects.filter(status='active').count(),
        'pending_deliveries': Donation.objects.filter(
            delivery_status='pending').count(),
    }
    return stats


def get_user_registration_trends(months=12):
    """Get user registration trends for the last N months"""
    now = timezone.now()
    trends = []
    
    for i in reversed(range(months)):
        start = (now - timedelta(days=30*(i+1)))
        end = (now - timedelta(days=30*i))
        
        count = CustomUser.objects.filter(
            date_joined__gte=start, 
            date_joined__lt=end
        ).count()
        
        trends.append({
            'month': start.strftime('%b %Y'),
            'count': count
        })
    
    return trends


def get_donation_trends(months=12):
    """Get donation trends for the last N months"""
    now = timezone.now()
    trends = []
    
    for i in reversed(range(months)):
        start = (now - timedelta(days=30*(i+1)))
        end = (now - timedelta(days=30*i))
        
        donations = Donation.objects.filter(
            donated_at__gte=start, 
            donated_at__lt=end
        )
        
        total_amount = donations.aggregate(total=Sum('amount'))['total'] or 0
        count = donations.count()
        
        trends.append({
            'month': start.strftime('%b %Y'),
            'count': count,
            'amount': float(total_amount)
        })
    
    return trends


def get_user_type_distribution():
    """Get user type distribution for pie chart"""
    distribution = CustomUser.objects.values('user_type').annotate(
        count=Count('id')
    ).order_by('user_type')
    
    return {
        'labels': [item['user_type'] for item in distribution],
        'data': [item['count'] for item in distribution]
    }


def get_donation_type_distribution():
    """Get donation type distribution for bar chart"""
    distribution = Donation.objects.values('donation_type').annotate(
        count=Count('id')
    ).order_by('donation_type')
    
    return {
        'labels': [item['donation_type'] for item in distribution],
        'data': [item['count'] for item in distribution]
    }


def get_recent_activity(limit=5):
    """Get recent activity across the platform"""
    recent_users = CustomUser.objects.order_by('-date_joined')[:limit]
    recent_donations = Donation.objects.select_related(
        'donor', 'foodbank'
    ).order_by('-donated_at')[:limit]
    recent_requests = FoodBankRequest.objects.select_related(
        'foodbank'
    ).order_by('-created_at')[:limit]
    
    return {
        'users': recent_users,
        'donations': recent_donations,
        'requests': recent_requests
    }


def get_priority_requests():
    """Get high priority and urgent requests"""
    return FoodBankRequest.objects.filter(
        priority__in=['high', 'urgent'],
        status='active'
    ).select_related('foodbank').order_by('-priority', '-created_at')


def get_overdue_requests():
    """Get overdue requests"""
    now = timezone.now()
    return FoodBankRequest.objects.filter(
        deadline__lt=now,
        status='active'
    ).select_related('foodbank').order_by('deadline')


def format_chart_data(data, labels_key='labels', data_key='data'):
    """Format data for Chart.js"""
    return {
        'labels': json.dumps(data.get(labels_key, [])),
        'data': json.dumps(data.get(data_key, []))
    }


def calculate_fulfillment_rate():
    """Calculate overall request fulfillment rate"""
    total_requests = FoodBankRequest.objects.count()
    fulfilled_requests = FoodBankRequest.objects.filter(status='fulfilled').count()
    
    if total_requests == 0:
        return 0
    
    return (fulfilled_requests / total_requests) * 100


def get_top_performers(limit=5):
    """Get top performing donors and food banks"""
    top_donors = CustomUser.objects.filter(
        user_type='DONOR'
    ).annotate(
        donation_count=Count('donation'),
        total_amount=Sum('donation__amount')
    ).order_by('-total_amount')[:limit]
    
    top_foodbanks = CustomUser.objects.filter(
        user_type='FOODBANK'
    ).annotate(
        donation_count=Count('foodbank_profile__donation'),
        request_count=Count('foodbank_profile__requests')
    ).order_by('-donation_count')[:limit]
    
    return {
        'donors': top_donors,
        'foodbanks': top_foodbanks
    }


def get_neutral_status(entity_type, raw_status, context=None):
    """
    Map user-facing status to neutral admin label.
    entity_type: 'unspecified'|'subsidized'|'direct'|'specified'
    context: optional dict with extra info (e.g. recipient_status, delivery_status)
    """
    if not raw_status:
        return 'Pending'
    raw = str(raw_status).lower().strip()
    ctx = context or {}

    if entity_type == 'unspecified':
        # foodbank_status + recipient_status combinations
        fb = ctx.get('foodbank_status', raw)
        rec = ctx.get('recipient_status', '')
        if 'received' in str(rec).lower():
            return 'Received by recipient'
        if 'accepted_by_recipient' in str(rec).lower():
            return 'Claimed by recipient'
        if 'declined_by_recipient' in str(rec).lower():
            return 'Declined by recipient'
        if 'accepted_by_foodbank' in str(fb).lower():
            return 'Accepted by foodbank (available for recipient)'
        if 'pending_foodbank' in str(fb).lower():
            return 'Pending foodbank review'
        if 'declined_by_foodbank' in str(fb).lower():
            return 'Declined by foodbank'
        return raw.replace('_', ' ').title()

    if entity_type == 'subsidized':
        if ctx.get('accepted_by_recipient') and str(ctx.get('delivery_status', '')).lower() == 'delivered':
            return 'Received by recipient'
        if ctx.get('accepted_by_recipient'):
            return 'Claimed by recipient'
        if ctx.get('declined_by_recipient'):
            return 'Declined by recipient'
        mapping = {
            'pending': 'Pending foodbank review',
            'accepted': 'Accepted by foodbank',
            'fulfilled': 'Fulfilled',
            'declined': 'Declined by foodbank',
        }
        return mapping.get(raw, raw.replace('_', ' ').title())

    if entity_type == 'direct':
        # FoodBankRequest status_label
        mapping = {
            'sent to donors': 'Published to donors',
            'donation made': 'Donation received by foodbank',
            'fulfilled': 'Fulfilled',
            'partially fulfilled': 'Partially fulfilled',
            'declined': 'Declined by donor',
        }
        return mapping.get(raw, raw.replace('_', ' ').title())

    if entity_type == 'specified':
        if raw == 'declined':
            req_obj = ctx.get('request_obj')
            if req_obj:
                if getattr(req_obj, 'recipient_declined_request', False):
                    return 'Declined by recipient'
                if getattr(req_obj, 'was_declined_by_foodbank', lambda: False)():
                    return 'Declined by foodbank'
            return 'Declined by recipient or foodbank'
        mapping = {
            'pending': 'Submitted to foodbank',
            'submitted': 'Published to donors',
            'donation_received': 'Donation received by foodbank',
            'assigned': 'Assigned to foodbank',
            'awaiting_recipient': 'Awaiting recipient response',
            'partial': 'Partially fulfilled',
            'fulfilled': 'Received by recipient',
            'acknowledged': 'Received by recipient',
        }
        return mapping.get(raw, raw.replace('_', ' ').title())

    return raw.replace('_', ' ').title()


def export_data_to_dict(queryset, fields):
    """Convert queryset to dictionary for export"""
    data = []
    for obj in queryset:
        row = {}
        for field in fields:
            if '.' in field:
                # Handle related fields
                parts = field.split('.')
                value = obj
                for part in parts:
                    value = getattr(value, part, '')
                    if value is None:
                        value = ''
                row[field] = value
            else:
                row[field] = getattr(obj, field, '')
        data.append(row)
    return data
