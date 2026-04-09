from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.password_validation import validate_password
import re

class StrongPasswordValidator:
    """
    Custom password validator that enforces strong password requirements.
    """
    
    def __init__(self, min_length=8, require_uppercase=True, require_lowercase=True, 
                 require_digits=True, require_special_chars=True):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special_chars = require_special_chars
    
    def validate(self, password, user=None):
        errors = []
        
        # Check minimum length
        if len(password) < self.min_length:
            errors.append(
                _('Password must be at least %(min_length)d characters long.') % 
                {'min_length': self.min_length}
            )
        
        # Check for uppercase letters
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append(_('Password must contain at least one uppercase letter.'))
        
        # Check for lowercase letters
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append(_('Password must contain at least one lowercase letter.'))
        
        # Check for digits
        if self.require_digits and not re.search(r'\d', password):
            errors.append(_('Password must contain at least one digit.'))
        
        # Check for special characters
        if self.require_special_chars and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            errors.append(_('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?).'))
        
        # Check for common weak patterns
        if re.search(r'(.)\1{2,}', password):
            errors.append(_('Password cannot contain more than 2 consecutive identical characters.'))
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', '12345678', 'qwerty', 'abc123', 'password123',
            'admin', 'letmein', 'welcome', 'monkey', 'dragon', 'master'
        ]
        if password.lower() in weak_passwords:
            errors.append(_('This password is too common. Please choose a stronger password.'))
        
        # Check for sequential patterns
        if re.search(r'(?:abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            errors.append(_('Password cannot contain sequential letters (abc, bcd, etc.).'))
        
        if re.search(r'(?:123|234|345|456|567|678|789|012)', password):
            errors.append(_('Password cannot contain sequential numbers (123, 234, etc.).'))
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        help_texts = [
            _('Your password must contain:'),
            _('• At least %(min_length)d characters') % {'min_length': self.min_length},
        ]
        
        if self.require_uppercase:
            help_texts.append(_('• At least one uppercase letter (A-Z)'))
        if self.require_lowercase:
            help_texts.append(_('• At least one lowercase letter (a-z)'))
        if self.require_digits:
            help_texts.append(_('• At least one digit (0-9)'))
        if self.require_special_chars:
            help_texts.append(_('• At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)'))
        
        help_texts.extend([
            _('• No more than 2 consecutive identical characters'),
            _('• No sequential patterns (abc, 123, etc.)'),
            _('• No common weak passwords')
        ])
        
        return ' '.join(help_texts)

# Create a default strong password validator instance
strong_password_validator = StrongPasswordValidator()

# Create a callable function for Django forms
def validate_strong_password(password):
    """
    Callable function that Django forms can use as a validator.
    """
    strong_password_validator.validate(password)

# Django password validator class for AUTH_PASSWORD_VALIDATORS
class DjangoStrongPasswordValidator:
    """
    Django-compatible password validator for AUTH_PASSWORD_VALIDATORS.
    """
    
    def __init__(self, min_length=8):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        strong_password_validator.validate(password, user)
    
    def get_help_text(self):
        return strong_password_validator.get_help_text()

class PasswordStrengthMeter:
    """
    Helper class to provide password strength feedback.
    """
    
    @staticmethod
    def get_strength(password):
        """
        Calculate password strength score (0-100).
        """
        score = 0
        
        # Length contribution (up to 25 points)
        if len(password) >= 8:
            score += 10
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 5
        
        # Character variety contribution (up to 40 points)
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            score += 10
        
        # Complexity contribution (up to 35 points)
        # Bonus for mixed case
        if re.search(r'[a-z]', password) and re.search(r'[A-Z]', password):
            score += 5
        
        # Bonus for letters and numbers
        if re.search(r'[a-zA-Z]', password) and re.search(r'\d', password):
            score += 5
        
        # Bonus for letters and special characters
        if re.search(r'[a-zA-Z]', password) and re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            score += 5
        
        # Bonus for numbers and special characters
        if re.search(r'\d', password) and re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            score += 5
        
        # Bonus for all three types
        if (re.search(r'[a-z]', password) and re.search(r'[A-Z]', password) and 
            re.search(r'\d', password) and re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password)):
            score += 15
        
        # Penalties for weak patterns
        if re.search(r'(.)\1{2,}', password):
            score -= 10
        
        if re.search(r'(?:abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            score -= 15
        
        if re.search(r'(?:123|234|345|456|567|678|789|012)', password):
            score -= 15
        
        return max(0, min(100, score))
    
    @staticmethod
    def get_strength_label(score):
        """
        Get human-readable strength label.
        """
        if score >= 80:
            return 'Very Strong'
        elif score >= 60:
            return 'Strong'
        elif score >= 40:
            return 'Moderate'
        elif score >= 20:
            return 'Weak'
        else:
            return 'Very Weak'
    
    @staticmethod
    def get_strength_color(score):
        """
        Get CSS color class for strength indicator.
        """
        if score >= 80:
            return 'text-success'
        elif score >= 60:
            return 'text-info'
        elif score >= 40:
            return 'text-warning'
        elif score >= 20:
            return 'text-danger'
        else:
            return 'text-danger'
