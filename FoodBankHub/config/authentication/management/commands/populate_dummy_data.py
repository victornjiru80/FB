from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import random
from authentication.models import (
    CustomUser, DonorProfile, FoodBankProfile, RecipientProfile,
    FoodBankRequest, Donation, Notification
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate the database with dummy data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new dummy data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Donation.objects.all().delete()
            FoodBankRequest.objects.all().delete()
            Notification.objects.all().delete()
            DonorProfile.objects.all().delete()
            FoodBankProfile.objects.all().delete()
            RecipientProfile.objects.all().delete()
            CustomUser.objects.filter(is_superuser=False).delete()

        self.stdout.write('Creating dummy users and profiles...')
        
        # Create dummy donors
        donors = []
        donor_emails = [
            'john.doe@example.com',
            'jane.smith@example.com', 
            'mike.johnson@example.com',
            'sarah.williams@example.com',
            'david.brown@example.com',
            'lisa.davis@example.com',
            'chris.miller@example.com',
            'emma.wilson@example.com',
            'alex.taylor@example.com',
            'maria.garcia@example.com'
        ]
        
        for email in donor_emails:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='testpass123',
                    user_type='DONOR'
                )
                profile = DonorProfile.objects.create(
                    user=user,
                    full_name=email.split('@')[0].replace('.', ' ').title(),
                    location=random.choice(['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret']),
                    phone_number=f'+2547{random.randint(10000000, 99999999)}',
                    preferred_donation_type=random.choice(['item', 'money', 'subsidized'])
                )
                donors.append(user)
                self.stdout.write(f'Created donor: {email}')

        # Create dummy food banks
        foodbanks = []
        foodbank_data = [
            ('Hope Food Bank Kenya', 'Nairobi', 'Providing hope through nutrition'),
            ('Community Care Food Bank', 'Mombasa', 'Caring for our community'),
            ('Harvest Hope Foundation', 'Kisumu', 'Harvesting hope for families'),
            ('Nourish Kenya', 'Nakuru', 'Nourishing communities across Kenya'),
            ('United Food Relief', 'Eldoret', 'United in fighting hunger'),
            ('Grace Food Ministry', 'Thika', 'Grace through food assistance'),
            ('Helping Hands Food Bank', 'Machakos', 'Lending helping hands to families')
        ]
        
        for name, location, description in foodbank_data:
            email = f"{name.lower().replace(' ', '.')}@foodbank.org"
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    password='testpass123',
                    user_type='FOODBANK'
                )
                profile = FoodBankProfile.objects.create(
                    user=user,
                    foodbank_name=name,
                    location=location,
                    description=description,
                    contact_person=f"{name.split()[0]} Manager",
                    phone_number=f'+2547{random.randint(10000000, 99999999)}',
                    registration_number=f'FB{random.randint(1000, 9999)}'
                )
                foodbanks.append(profile)
                self.stdout.write(f'Created food bank: {name}')

        # Create dummy food bank requests
        self.stdout.write('Creating food bank requests...')
        
        request_data = [
            ('Urgent Rice Donation Needed', 'We urgently need 500kg of rice to feed 200 families this week', 'urgent', 500, 'kg'),
            ('Cooking Oil Emergency', 'Emergency request for cooking oil to serve 150 families', 'urgent', 75, 'litres'),
            ('School Feeding Program Support', 'Need beans and maize for our school feeding program', 'high', 300, 'kg'),
            ('Weekly Food Distribution', 'Regular weekly food distribution requires various items', 'medium', 200, 'kg'),
            ('Elderly Care Program', 'Special nutrition needs for our elderly care program', 'high', 100, 'packets'),
            ('Children Nutrition Support', 'Nutritious food items needed for children under 5', 'urgent', 150, 'packets'),
            ('Community Kitchen Supplies', 'Basic food supplies for our community kitchen', 'medium', 250, 'kg'),
            ('Emergency Food Relief', 'Emergency food relief for flood-affected families', 'urgent', 400, 'kg'),
            ('Monthly Food Drive', 'Monthly food drive to support vulnerable families', 'low', 180, 'kg'),
            ('Ramadan Food Support', 'Special food packages for Ramadan support', 'medium', 120, 'packets'),
            ('Orphanage Food Supplies', 'Food supplies needed for local orphanage', 'high', 220, 'kg'),
            ('Widow Support Program', 'Food assistance for widows in our community', 'medium', 160, 'kg')
        ]
        
        requests = []
        for i, (title, description, priority, quantity, unit) in enumerate(request_data):
            foodbank = random.choice(foodbanks)
            created_at = timezone.now() - timedelta(days=random.randint(1, 30))
            deadline = created_at + timedelta(days=random.randint(7, 30))
            
            request = FoodBankRequest.objects.create(
                foodbank=foodbank,
                title=title,
                description=description,
                priority=priority,
                quantity_needed=quantity,
                quantity_unit=unit,
                deadline=deadline,
                created_at=created_at,
                status=random.choice(['active', 'active', 'active', 'fulfilled']) # More active than fulfilled
            )
            requests.append(request)
            self.stdout.write(f'Created request: {title}')

        # Create dummy donations
        self.stdout.write('Creating donations...')
        
        item_names = [
            'Rice', 'Beans', 'Maize', 'Cooking Oil', 'Sugar', 'Salt', 
            'Wheat Flour', 'Milk Powder', 'Tea Leaves', 'Bread',
            'Potatoes', 'Onions', 'Tomatoes', 'Cabbage', 'Carrots'
        ]
        
        # Create donations for the last 6 months
        for _ in range(80):  # Create 80 donations
            donor = random.choice(donors)
            foodbank = random.choice(foodbanks)
            donation_type = random.choice(['item', 'money', 'subsidized'])
            donated_at = timezone.now() - timedelta(days=random.randint(1, 180))
            
            # Sometimes link donation to a specific request
            linked_request = None
            if random.choice([True, False, False]):  # 33% chance of being linked to request
                possible_requests = [r for r in requests if r.foodbank == foodbank and r.created_at <= donated_at]
                if possible_requests:
                    linked_request = random.choice(possible_requests)
            
            if donation_type == 'item':
                item_name = random.choice(item_names)
                quantity = random.randint(5, 200)
                unit = random.choice(['kg', 'packets', 'litres', 'items'])
                
                donation = Donation.objects.create(
                    donor=donor,
                    foodbank=foodbank,
                    foodbank_request=linked_request,
                    donation_type=donation_type,
                    item_name=item_name,
                    quantity=quantity,
                    quantity_unit=unit,
                    delivery_method=random.choice(['pickup', 'dropoff']),
                    delivery_status=random.choice(['pending', 'scheduled', 'delivered']),
                    donated_at=donated_at,
                    message=f"Hope this helps your {foodbank.foodbank_name}!"
                )
                
            elif donation_type == 'money':
                amount = random.randint(500, 20000)  # KES 500 to 20,000
                
                donation = Donation.objects.create(
                    donor=donor,
                    foodbank=foodbank,
                    foodbank_request=linked_request,
                    donation_type=donation_type,
                    amount=amount,
                    delivery_method='pickup',
                    delivery_status='delivered',
                    donated_at=donated_at,
                    message=f"Monetary donation to support your cause"
                )
                
            else:  # subsidized
                subsidized_price = random.randint(200, 5000)  # KES 200 to 5,000
                
                donation = Donation.objects.create(
                    donor=donor,
                    foodbank=foodbank,
                    foodbank_request=linked_request,
                    donation_type=donation_type,
                    subsidized_price=subsidized_price,
                    delivery_method=random.choice(['pickup', 'dropoff']),
                    delivery_status=random.choice(['pending', 'scheduled', 'delivered']),
                    donated_at=donated_at,
                    message=f"Subsidized goods donation"
                )

        # Create some notifications
        self.stdout.write('Creating notifications...')
        
        all_users = list(User.objects.all())
        notification_types = [
            'acknowledgement', 'donation_received', 'request_fulfilled', 
            'urgent_request', 'system', 'new_donor'
        ]
        
        for _ in range(50):  # Create 50 notifications
            user = random.choice(all_users)
            notification_type = random.choice(notification_types)
            
            messages = {
                'acknowledgement': 'Thank you for your generous donation!',
                'donation_received': 'New donation received from a generous donor',
                'request_fulfilled': 'Your urgent request has been fulfilled!',
                'urgent_request': 'New urgent request needs your attention',
                'system': 'System maintenance scheduled for tonight',
                'new_donor': 'Welcome to FoodBank Hub community!'
            }
            
            Notification.objects.create(
                user=user,
                notification_type=notification_type,
                message=messages[notification_type],
                is_read=random.choice([True, False]),
                created_at=timezone.now() - timedelta(days=random.randint(1, 30))
            )

        # Update some requests to fulfilled status based on donations
        self.stdout.write('Updating request fulfillment status...')
        
        for request in requests:
            if request.status == 'active':
                # Check if donations have fulfilled this request
                if request.should_auto_fulfill():
                    request.status = 'fulfilled'
                    request.save()
                    self.stdout.write(f'Auto-fulfilled request: {request.title}')

        # Print summary
        total_users = User.objects.count()
        total_donors = DonorProfile.objects.count()
        total_foodbanks = FoodBankProfile.objects.count()
        total_requests = FoodBankRequest.objects.count()
        total_donations = Donation.objects.count()
        total_notifications = Notification.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Dummy data created successfully!\n'
                f'📊 Summary:\n'
                f'   - Users: {total_users}\n'
                f'   - Donors: {total_donors}\n'
                f'   - Food Banks: {total_foodbanks}\n'
                f'   - Requests: {total_requests}\n'
                f'   - Donations: {total_donations}\n'
                f'   - Notifications: {total_notifications}\n'
            )
        )
        
        self.stdout.write(
            self.style.WARNING(
                f'\n🔐 Login credentials for testing:\n'
                f'   - Donor: john.doe@example.com / testpass123\n'
                f'   - Food Bank: hope.food.bank.kenya@foodbank.org / testpass123\n'
            )
        )
