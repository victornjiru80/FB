from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from authentication.models import FoodBankSubscription, Notification


class Command(BaseCommand):
    help = 'Send trial expiration reminder emails (7 days, 3 days, 1 day before expiration)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually sending emails',
        )
        parser.add_argument(
            '--days',
            type=int,
            choices=[7, 3, 1],
            help='Send reminders for specific days before expiration (7, 3, or 1)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_days = options.get('days')
        now = timezone.now()
        
        # Define reminder periods
        reminder_days = [7, 3, 1] if not specific_days else [specific_days]
        
        total_sent = 0
        
        for days in reminder_days:
            # Find trials expiring in X days
            target_date = now + timedelta(days=days)
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            expiring_trials = FoodBankSubscription.objects.filter(
                status='trial',
                trial_end_date__gte=start_of_day,
                trial_end_date__lte=end_of_day
            ).select_related('foodbank', 'foodbank__user')
            
            if expiring_trials.exists():
                self.stdout.write(f'Found {expiring_trials.count()} trials expiring in {days} day(s)...')
                
                for subscription in expiring_trials:
                    try:
                        self.send_reminder_email(subscription, days, dry_run)
                        
                        # Create in-app notification
                        if not dry_run:
                            Notification.objects.create(
                                user=subscription.foodbank.user,
                                notification_type='trial_reminder',
                                message=f'Your free trial expires in {days} day(s). Subscribe now to avoid interruption.'
                            )
                        
                        total_sent += 1
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'{"[DRY RUN] " if dry_run else ""}Sent {days}-day reminder to {subscription.foodbank.foodbank_name}'
                            )
                        )
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Error sending reminder to {subscription.foodbank.foodbank_name}: {str(e)}'
                            )
                        )
            else:
                self.stdout.write(f'No trials expiring in {days} day(s).')
        
        if total_sent > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'{"[DRY RUN] " if dry_run else ""}Successfully sent {total_sent} reminder emails!'
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS('No reminder emails needed today.'))

    def send_reminder_email(self, subscription, days_remaining, dry_run=False):
        """Send trial expiration reminder email"""
        foodbank = subscription.foodbank
        user = foodbank.user
        
        # Customize subject and urgency based on days remaining
        if days_remaining == 7:
            subject = 'Your FoodBankHub Trial Expires in 1 Week - Subscribe Now'
            urgency = 'one week'
            urgency_class = 'notice'
        elif days_remaining == 3:
            subject = 'Important: Your FoodBankHub Trial Expires in 3 Days'
            urgency = 'just 3 days'
            urgency_class = 'warning'
        else:  # 1 day
            subject = 'URGENT: Your FoodBankHub Trial Expires Tomorrow!'
            urgency = 'less than 24 hours'
            urgency_class = 'urgent'
        
        expiration_date = subscription.trial_end_date.strftime('%B %d, %Y at %I:%M %p')
        
        message = f"""
Dear {foodbank.contact_person},

This is a friendly reminder that your 90-day free trial for "{foodbank.foodbank_name}" on FoodBankHub expires in {urgency}.

TRIAL EXPIRATION: {expiration_date}

{"🚨 URGENT ACTION REQUIRED!" if days_remaining == 1 else "⚠️ ACTION REQUIRED:" if days_remaining == 3 else "📅 UPCOMING EXPIRATION:"}

In {urgency}, you will lose access to:
• Creating food requests for your community
• Receiving donations from generous donors
• Your food bank profile visibility
• Platform analytics and reports

DON'T LET YOUR IMPACT STOP!

Subscribe now to ensure uninterrupted service:

SUBSCRIPTION OPTIONS:
• Monthly Plan: KSH 2,000/month - Perfect for getting started
• Yearly Plan: KSH 10,000/year - Save KSH 14,000 (Best Value!)

QUICK SUBSCRIBE:
1. Visit: {settings.SITE_URL}/subscribe/
2. Choose your plan
3. Complete payment
4. Continue helping your community immediately!

WHY SUBSCRIBE?
✓ Unlimited food requests
✓ Connect with active donors
✓ Professional food bank profile
✓ Detailed impact reports
✓ Priority customer support
✓ Help more families in need

QUESTIONS?
Visit your subscription dashboard: {settings.SITE_URL}/subscription/status/
Contact support: {settings.SITE_URL}/support/

{"Your community is counting on you - don't let them down!" if days_remaining == 1 else "Your community needs you - secure your subscription today!" if days_remaining == 3 else "Plan ahead and secure your subscription to avoid any interruption in service."}

Best regards,
The FoodBankHub Team

P.S. {"This is your final reminder before expiration!" if days_remaining == 1 else "We'll send you another reminder as your trial approaches expiration." if days_remaining > 1 else ""}

---
This is an automated email. Please do not reply directly to this message.
For support, visit: {settings.SITE_URL}/support/
        """
        
        if dry_run:
            self.stdout.write(f'[DRY RUN] Would send {days_remaining}-day reminder to: {user.email}')
            return
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            self.stdout.write(f'✓ {days_remaining}-day reminder sent to {user.email}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to send reminder to {user.email}: {str(e)}')
            )
