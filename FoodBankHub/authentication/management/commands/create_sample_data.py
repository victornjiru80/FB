from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from authentication.models import CustomUser, FoodBankProfile, FoodBankRequest

class Command(BaseCommand):
    help = 'Create sample foodbank requests for testing'

    def handle(self, *args, **options):
        # Create sample foodbanks if they don't exist
        sample_foodbanks = [
            {
                'email': 'community@hope.org',
                'foodbank_name': 'Hope Community Food Bank',
                'contact_person': 'Sarah Johnson',
                'address': '123 Main Street, Downtown',
            },
            {
                'email': 'help@neighbors.org',
                'foodbank_name': 'Neighbors Helping Neighbors',
                'contact_person': 'Michael Brown',
                'address': '456 Oak Avenue, Westside',
            },
            {
                'email': 'support@family.org',
                'foodbank_name': 'Family Support Center',
                'contact_person': 'Lisa Davis',
                'address': '789 Pine Road, Eastside',
            },
            {
                'email': 'care@community.org',
                'foodbank_name': 'Community Care Network',
                'contact_person': 'Robert Wilson',
                'address': '321 Elm Street, Northside',
            },
            {
                'email': 'assist@local.org',
                'foodbank_name': 'Local Assistance Program',
                'contact_person': 'Jennifer Lee',
                'address': '654 Maple Drive, Southside',
            },
            {
                'email': 'aid@charity.org',
                'foodbank_name': 'Charity Aid Foundation',
                'contact_person': 'David Miller',
                'address': '987 Cedar Lane, Central',
            },
        ]

        for foodbank_data in sample_foodbanks:
            user, created = CustomUser.objects.get_or_create(
                email=foodbank_data['email'],
                defaults={
                    'user_type': 'FOODBANK',
                    'phone_number': '555-0123',
                    'password': 'testpass123'
                }
            )
            
            if created:
                user.set_password('testpass123')
                user.save()
                
                FoodBankProfile.objects.create(
                    user=user,
                    foodbank_name=foodbank_data['foodbank_name'],
                    contact_person=foodbank_data['contact_person'],
                    address=foodbank_data['address']
                )
                
                self.stdout.write(f"Created foodbank: {foodbank_data['foodbank_name']}")

        # Create sample requests
        sample_requests = [
            {
                'foodbank_name': 'Hope Community Food Bank',
                'title': 'Urgent Need for Canned Goods',
                'description': 'We are running low on canned vegetables and fruits. Any donations would be greatly appreciated to help families in our community.',
                'priority': 'urgent',
                'quantity_needed': 200,
                'quantity_unit': 'cans',
                'deadline': timezone.now() + timedelta(days=3)
            },
            {
                'foodbank_name': 'Neighbors Helping Neighbors',
                'title': 'Fresh Produce Request',
                'description': 'Looking for fresh vegetables and fruits to provide healthy meals for children and families. Local produce preferred.',
                'priority': 'high',
                'quantity_needed': 50,
                'quantity_unit': 'kg',
                'deadline': timezone.now() + timedelta(days=7)
            },
            {
                'foodbank_name': 'Family Support Center',
                'title': 'Baby Food and Formula',
                'description': 'Critical need for baby food, formula, and diapers. Many families with infants are struggling to provide basic necessities.',
                'priority': 'urgent',
                'quantity_needed': 100,
                'quantity_unit': 'items',
                'deadline': timezone.now() + timedelta(days=2)
            },
            {
                'foodbank_name': 'Community Care Network',
                'title': 'Bread and Bakery Items',
                'description': 'Daily need for fresh bread, pastries, and bakery items. We serve breakfast to over 200 people each morning.',
                'priority': 'medium',
                'quantity_needed': 150,
                'quantity_unit': 'items',
                'deadline': timezone.now() + timedelta(days=5)
            },
            {
                'foodbank_name': 'Local Assistance Program',
                'title': 'Protein-Rich Foods',
                'description': 'Seeking donations of meat, fish, eggs, and legumes to provide protein-rich meals for growing children and families.',
                'priority': 'high',
                'quantity_needed': 75,
                'quantity_unit': 'kg',
                'deadline': timezone.now() + timedelta(days=4)
            },
            {
                'foodbank_name': 'Charity Aid Foundation',
                'title': 'Hygiene and Personal Care',
                'description': 'Need for soap, shampoo, toothpaste, and other personal care items. These are essential but often overlooked donations.',
                'priority': 'medium',
                'quantity_needed': 300,
                'quantity_unit': 'items',
                'deadline': timezone.now() + timedelta(days=10)
            },
        ]

        for request_data in sample_requests:
            try:
                foodbank = FoodBankProfile.objects.get(foodbank_name=request_data['foodbank_name'])
                
                FoodBankRequest.objects.get_or_create(
                    foodbank=foodbank,
                    title=request_data['title'],
                    defaults={
                        'description': request_data['description'],
                        'priority': request_data['priority'],
                        'quantity_needed': request_data['quantity_needed'],
                        'quantity_unit': request_data['quantity_unit'],
                        'deadline': request_data['deadline']
                    }
                )
                
                self.stdout.write(f"Created request: {request_data['title']}")
                
            except FoodBankProfile.DoesNotExist:
                self.stdout.write(f"Foodbank not found: {request_data['foodbank_name']}")

        self.stdout.write(self.style.SUCCESS('Successfully created sample foodbank requests')) 