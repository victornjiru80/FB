from django.core.management.base import BaseCommand
from django.db import connections
from django.conf import settings
import sqlite3
import psycopg
from authentication.models import CustomUser, DonorProfile, FoodBankProfile

class Command(BaseCommand):
    help = 'Migrate data from SQLite to PostgreSQL manually'

    def handle(self, *args, **options):
        # Connect to SQLite
        sqlite_path = settings.BASE_DIR / 'db.sqlite3'
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        self.stdout.write('Starting manual migration...')
        
        try:
            # Migrate CustomUser
            sqlite_cursor.execute("""
                SELECT id, email, user_type, phone_number, first_name, last_name, 
                       is_active, is_staff, is_superuser, date_joined, password
                FROM authentication_customuser
            """)
            
            users = sqlite_cursor.fetchall()
            self.stdout.write(f'Found {len(users)} users to migrate')
            
            for user_data in users:
                user, created = CustomUser.objects.get_or_create(
                    email=user_data[1],
                    defaults={
                        'user_type': user_data[2],
                        'phone_number': user_data[3] or '',
                        'first_name': user_data[4] or '',
                        'last_name': user_data[5] or '',
                        'is_active': user_data[6],
                        'is_staff': user_data[7],
                        'is_superuser': user_data[8],
                        'date_joined': user_data[9],
                        'password': user_data[10],
                    }
                )
                if created:
                    self.stdout.write(f'Migrated user: {user.email}')
            
            # Migrate DonorProfile
            sqlite_cursor.execute("""
                SELECT user_id, full_name, is_organization, organization_name
                FROM authentication_donorprofile
            """)
            
            donor_profiles = sqlite_cursor.fetchall()
            self.stdout.write(f'Found {len(donor_profiles)} donor profiles to migrate')
            
            for profile_data in donor_profiles:
                try:
                    user = CustomUser.objects.get(id=profile_data[0])
                    profile, created = DonorProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'full_name': profile_data[1] or '',
                            'is_organization': profile_data[2] or False,
                            'organization_name': profile_data[3] or '',
                        }
                    )
                    if created:
                        self.stdout.write(f'Migrated donor profile: {profile.full_name}')
                except CustomUser.DoesNotExist:
                    self.stdout.write(f'User not found for donor profile: {profile_data[0]}')
            
            # Migrate FoodBankProfile
            sqlite_cursor.execute("""
                SELECT user_id, foodbank_name, contact_person, address, service_type, 
                       is_approved, approval_date, application_date
                FROM authentication_foodbankprofile
            """)
            
            foodbank_profiles = sqlite_cursor.fetchall()
            self.stdout.write(f'Found {len(foodbank_profiles)} foodbank profiles to migrate')
            
            for profile_data in foodbank_profiles:
                try:
                    user = CustomUser.objects.get(id=profile_data[0])
                    profile, created = FoodBankProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'foodbank_name': profile_data[1] or '',
                            'contact_person': profile_data[2] or '',
                            'address': profile_data[3] or '',
                            'service_type': profile_data[4] or 'both',
                            'is_approved': profile_data[5] or 'pending',
                            'approval_date': profile_data[6],
                            'application_date': profile_data[7],
                        }
                    )
                    if created:
                        self.stdout.write(f'Migrated foodbank profile: {profile.foodbank_name}')
                except CustomUser.DoesNotExist:
                    self.stdout.write(f'User not found for foodbank profile: {profile_data[0]}')
            
            self.stdout.write(self.style.SUCCESS('Migration completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Migration failed: {str(e)}'))
        finally:
            sqlite_conn.close()
