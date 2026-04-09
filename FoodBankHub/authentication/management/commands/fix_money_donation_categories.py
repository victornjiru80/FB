"""
One-time fix: set donation_category to the request type (food/non_food) for money donations
that are linked to a foodbank request but currently have category 'monetary'.
Run: python manage.py fix_money_donation_categories
"""
from django.core.management.base import BaseCommand
from authentication.models import Donation


class Command(BaseCommand):
    help = "Set donation_category to request type (food/non_food) for money donations linked to a request"

    def handle(self, *args, **options):
        qs = Donation.objects.filter(
            donation_type='money',
            donation_category='monetary',
            foodbank_request__isnull=False,
        ).select_related('foodbank_request', 'foodbank_request__original_request')
        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No money donations with category "monetary" linked to a request.'))
            return
        for donation in qs:
            donation.save()  # Model save() normalizes category from linked request
            self.stdout.write(f'  Donation {donation.id}: category -> {donation.donation_category}')
        self.stdout.write(self.style.SUCCESS(f'Updated {count} donation(s) to match foodbank request category.'))
