from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from authentication.models import FoodBankSubscription


class Command(BaseCommand):
    help = 'Fix trial_end_date for existing subscriptions'

    def handle(self, *args, **options):
        subscriptions = FoodBankSubscription.objects.filter(trial_end_date__isnull=True)
        count = subscriptions.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No subscriptions need fixing!'))
            return
        
        self.stdout.write(f'Found {count} subscriptions without trial_end_date')
        
        for subscription in subscriptions:
            # Set trial_end_date to 90 days from trial_start_date
            if subscription.trial_start_date:
                subscription.trial_end_date = subscription.trial_start_date + timedelta(days=90)
                subscription.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Fixed subscription for {subscription.foodbank.foodbank_name}: '
                        f'Trial ends {subscription.trial_end_date.strftime("%Y-%m-%d")}'
                    )
                )
            else:
                # If no trial_start_date, use created_at
                subscription.trial_start_date = subscription.created_at
                subscription.trial_end_date = subscription.created_at + timedelta(days=90)
                subscription.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Fixed subscription for {subscription.foodbank.foodbank_name}: '
                        f'Trial ends {subscription.trial_end_date.strftime("%Y-%m-%d")}'
                    )
                )
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully fixed {count} subscriptions!'))
