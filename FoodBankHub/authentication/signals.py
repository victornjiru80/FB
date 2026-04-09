from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from datetime import timedelta
from .models import FoodBankProfile, FoodBankSubscription, AdminLoginLog


@receiver(post_save, sender=FoodBankProfile)
def create_subscription_for_foodbank(sender, instance, created, **kwargs):
    """
    Automatically create a subscription with 3-month trial when a food bank is created.
    """
    if created:
        # Create subscription with trial status and set trial end date
        now = timezone.now()
        FoodBankSubscription.objects.create(
            foodbank=instance,
            status='trial',
            plan='trial',
            trial_start_date=now,
            trial_end_date=now + timedelta(days=90)
        )



@receiver(user_logged_in)
def log_admin_login(sender, request, user, **kwargs):
    """Log admin login activities"""
    if user.is_staff or user.user_type == 'ADMIN':
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        # Ensure ip_address is always non-null (AdminLoginLog.ip_address is NOT NULL)
        if not ip_address:
            ip_address = '0.0.0.0'
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create login log
        AdminLoginLog.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            session_key=request.session.session_key,
            login_successful=True
        )


@receiver(user_logged_out)
def log_admin_logout(sender, request, user, **kwargs):
    """Update login log with logout time"""
    if user and (user.is_staff or user.user_type == 'ADMIN'):
        # Find the most recent login log for this user
        try:
            login_log = AdminLoginLog.objects.filter(
                user=user,
                logout_time__isnull=True
            ).latest('login_time')
            
            login_log.logout_time = timezone.now()
            login_log.calculate_session_duration()
        except AdminLoginLog.DoesNotExist:
            pass
