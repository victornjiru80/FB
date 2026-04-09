from .models import Notification

def navbar_context(request):
    """Add navbar-related context to all templates"""
    context = {}
    
    if request.user.is_authenticated:
        # Add unread notification count for all authenticated users
        context['unread_notifications_count'] = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    
    return context
