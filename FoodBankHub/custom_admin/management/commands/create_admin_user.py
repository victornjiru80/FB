from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class Command(BaseCommand):
    help = 'Create an admin user for the custom admin dashboard'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Admin email address', required=True)
        parser.add_argument('--password', type=str, help='Admin password')
        parser.add_argument('--phone', type=str, help='Admin phone number', required=True)

    def handle(self, *args, **options):
        email = options['email']
        password = options.get('password')
        phone = options['phone']

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'User with email {email} already exists!')
            )
            return

        # Get password if not provided
        if not password:
            import getpass
            password = getpass.getpass('Enter password: ')
            confirm_password = getpass.getpass('Confirm password: ')
            
            if password != confirm_password:
                self.stdout.write(
                    self.style.ERROR('Passwords do not match!')
                )
                return

        try:
            # Create admin user
            user = User.objects.create_user(
                email=email,
                password=password,
                phone_number=phone,
                user_type='ADMIN',
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created admin user: {email}\n'
                    f'User Type: {user.user_type}\n'
                    f'Staff Status: {user.is_staff}\n'
                    f'Superuser Status: {user.is_superuser}\n'
                    f'You can now access the custom admin at /dashboard/'
                )
            )
            
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating user: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )
