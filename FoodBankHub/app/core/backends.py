# Import the default authentication backend from Django
from django.contrib.auth.backends import ModelBackend

# Import your custom user model
from .models import CustomUser

class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their email address
    instead of their username.
    """
    def authenticate(self, request, email=None, password=None, **kwargs):
        # Ensure both email and password are provided
        if email is None or password is None:
            return None
        
        try:
            # Try to find the user by email, case-insensitive
            user = CustomUser.objects.get(email__iexact=email)
            
            # Check if the password is correct and the user is allowed to authenticate
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        
        # If no user exists with that email, return None
        except CustomUser.DoesNotExist:
            return None

