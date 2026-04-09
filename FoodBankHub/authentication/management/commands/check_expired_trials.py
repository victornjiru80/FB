from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from authentication.models import FoodBankSubscription, Notification


class Command(BaseCommand):
    help = 'Check for expired trials and send email notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually sending emails',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        # Find trials that expired today (within last 24 hours)
        yesterday = now - timedelta(days=1)
        expired_trials = FoodBankSubscription.objects.filter(
            status='trial',
            trial_end_date__gte=yesterday,
            trial_end_date__lt=now
        ).select_related('foodbank', 'foodbank__user')
        
        if not expired_trials.exists():
            self.stdout.write(self.style.SUCCESS('No trials expired today.'))
            return
        
        self.stdout.write(f'Found {expired_trials.count()} expired trials to process...')
        
        for subscription in expired_trials:
            try:
                # Update subscription status to expired
                if not dry_run:
                    subscription.status = 'expired'
                    subscription.save()
                
                # Send expiration email
                self.send_expiration_email(subscription, dry_run)
                
                # Create in-app notification
                if not dry_run:
                    Notification.objects.create(
                        user=subscription.foodbank.user,
                        notification_type='subscription_expired',
                        message='Your 90-day free trial has expired. Subscribe now to continue using FoodBankHub.'
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{"[DRY RUN] " if dry_run else ""}Processed expired trial for {subscription.foodbank.foodbank_name}'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing {subscription.foodbank.foodbank_name}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{"[DRY RUN] " if dry_run else ""}Successfully processed {expired_trials.count()} expired trials!'
            )
        )

    def send_expiration_email(self, subscription, dry_run=False):
        """Send trial expiration email to food bank"""
        foodbank = subscription.foodbank
        user = foodbank.user
        
        subject = 'Your FoodBankHub Trial Has Expired - Subscribe to Continue'
        
        message = f"""
Dear {foodbank.contact_person},

Your 90-day free trial for "{foodbank.foodbank_name}" on FoodBankHub has expired as of {subscription.trial_end_date.strftime('%B %d, %Y')}.

WHAT THIS MEANS:
• You no longer have access to create food requests
• You cannot receive new donations through the platform
• Your food bank profile is no longer visible to donors
• All existing data and history remain safe and will be restored upon subscription

CONTINUE YOUR IMPACT:
Don't let this interruption stop your important work! Subscribe now to:
✓ Resume receiving donations from generous donors
✓ Create urgent food requests for your community
✓ Access detailed reports and analytics
✓ Maintain your professional food bank profile
✓ Connect with a network of active donors

SUBSCRIPTION OPTIONS:
• Monthly Plan: KSH 2,000/month
• Yearly Plan: KSH 10,000/year (Save KSH 14,000!)

SUBSCRIBE NOW:
Visit your subscription page: {settings.SITE_URL}/subscription/status/
Or subscribe directly: {settings.SITE_URL}/subscribe/

NEED HELP?
If you have any questions about your subscription or need assistance, please contact our support team.

Your community depends on your vital work. Don't let a lapsed subscription interrupt the flow of help to those who need it most.

Subscribe today and continue making a difference!

Best regards,
The FoodBankHub Team

---
This is an automated email. Please do not reply directly to this message.
For support, visit: {settings.SITE_URL}/support/
        """
        
        if dry_run:
            self.stdout.write(f'[DRY RUN] Would send email to: {user.email}')
            return
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            self.stdout.write(f'✓ Email sent to {user.email}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to send email to {user.email}: {str(e)}')
            )
