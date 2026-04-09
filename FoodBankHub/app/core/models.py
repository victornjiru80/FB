from django.contrib.auth.models import AbstractUser, BaseUserManager, User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now
from decimal import Decimal

# Shared choices for quantity units
QUANTITY_UNITS = [
    ('kg', 'Kilograms'),
    ('litres', 'Litres'),
    ('packets', 'Packets'),
    ('items', 'Items'),
    ('bags', 'Bags'),
    ('boxes', 'Boxes'),
    ('cans', 'Cans'),
    ('bottles', 'Bottles'),
    ('pieces', 'Pieces'),
    ('units', 'Units'),
    ('tons', 'Tons'),
    ('grams', 'Grams'),
    ('ml', 'Millilitres'),
    ('other', 'Other'),
]


class QuantityUnit(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    label = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.label

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'ADMIN')
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('DONOR', 'Donor'),
        ('FOODBANK', 'Foodbank'),
        ('RECIPIENT', 'Recipient'),
    ]

    username = None
    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_type', 'phone_number']

    def __str__(self):
        return self.email

class DonorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='donor_profile')
    full_name = models.CharField(max_length=255)
    is_organization = models.BooleanField(default=False)
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.organization_name if self.is_organization else self.full_name

class FoodBankProfile(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('food', 'Food Only'),
        ('non_food', 'Non-Food Only'),
        ('both', 'Food and Non-Food'),
    ]
    
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='foodbank_profile')
    foodbank_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES, default='both', help_text="What type of assistance does your food bank provide?")
    authority_picture = models.ImageField(upload_to='foodbank/authority/', blank=True, null=True)
    urgent_request_picture = models.ImageField(upload_to='foodbank/urgent_requests/', blank=True, null=True)
    additional_documents = models.FileField(upload_to='foodbank/documents/', blank=True, null=True, help_text="Upload any additional documentation (permits, certificates, etc.)")
    
    # Approval fields
    is_approved = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending')
    approval_date = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_foodbanks')
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection (if applicable)")
    application_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    # New fields for public profile page
    header_photo = models.ImageField(upload_to='foodbank/headers/', blank=True, null=True, help_text="Header image for your public profile page")
    about_text = models.TextField(blank=True, null=True, help_text="Tell donors about your food bank, mission, and impact")
    mission_statement = models.TextField(blank=True, null=True, help_text="Your organization's mission statement")
    contact_email = models.EmailField(blank=True, null=True, help_text="Public contact email for donors")
    contact_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Public contact phone number")
    website_url = models.URLField(blank=True, null=True, help_text="Your organization's website")
    established_year = models.PositiveIntegerField(blank=True, null=True, help_text="Year your food bank was established")
    
    def __str__(self):
        return f"{self.foodbank_name} ({self.get_is_approved_display()})"
    
    def is_pending_approval(self):
        return self.is_approved == 'pending'
    
    def is_approved_status(self):
        return self.is_approved == 'approved'
    
    def is_rejected_status(self):
        return self.is_approved == 'rejected'
    
    def authority_picture_exists(self):
        """Check if authority picture file exists on disk"""
        if self.authority_picture:
            try:
                return self.authority_picture.storage.exists(self.authority_picture.name)
            except:
                return False
        return False
    
    def urgent_request_picture_exists(self):
        """Check if urgent request picture file exists on disk"""
        if self.urgent_request_picture:
            try:
                return self.urgent_request_picture.storage.exists(self.urgent_request_picture.name)
            except:
                return False
        return False
    
    def additional_documents_exists(self):
        """Check if additional documents file exists on disk"""
        if self.additional_documents:
            try:
                return self.additional_documents.storage.exists(self.additional_documents.name)
            except:
                return False
        return False
    
    def is_profile_complete(self):
        """Check if the public profile has minimum required information"""
        required_fields = [self.header_photo, self.about_text, self.mission_statement]
        return all(field for field in required_fields)
    
    def get_profile_completion_percentage(self):
        """Calculate profile completion percentage"""
        total_fields = 7  # header_photo, about_text, mission_statement, contact_email, contact_phone, website_url, established_year
        completed_fields = sum([
            bool(self.header_photo),
            bool(self.about_text),
            bool(self.mission_statement),
            bool(self.contact_email),
            bool(self.contact_phone),
            bool(self.website_url),
            bool(self.established_year)
        ])
        return int((completed_fields / total_fields) * 100)

class FoodBankGalleryPhoto(models.Model):
    """Model for food bank gallery photos"""
    foodbank = models.ForeignKey(FoodBankProfile, on_delete=models.CASCADE, related_name='gallery_photos')
    photo = models.ImageField(upload_to='foodbank/gallery/', help_text="Photos showcasing your food bank's work and impact")
    caption = models.CharField(max_length=255, blank=True, null=True, help_text="Optional caption for the photo")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False, help_text="Feature this photo prominently on your profile")
    
    class Meta:
        ordering = ['-is_featured', '-uploaded_at']
    
    def __str__(self):
        return f"{self.foodbank.foodbank_name} - Gallery Photo {self.id}"
    
class RecipientProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='recipient_profile')
    full_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    is_organization = models.BooleanField(default=False)
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    consent_subsidized_goods = models.BooleanField(default=False)

    def __str__(self):
        return self.organization_name if self.is_organization else self.full_name
    
    
    
class RecipientRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
    ]
    recipient = models.ForeignKey(RecipientProfile, on_delete=models.CASCADE, related_name='requests')
    foodbank = models.ForeignKey(FoodBankProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='recipient_requests')
    title = models.CharField(max_length=255)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    quantity_unit = models.CharField(max_length=20, blank=True, null=True)
    delivery_method = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending') 
    linked_donor_request = models.ForeignKey('FoodbankRequest', on_delete=models.SET_NULL, null=True, blank=True)
    fulfillment_notes = models.TextField(blank=True, null=True)
    declined_by = models.ManyToManyField("FoodBankProfile", related_name="declined_requests", blank=True)

    

class FoodBankRequest(models.Model):

    DONATION_TYPE_CHOICES = [
        ('food', 'Food'),
        ('non_food', 'Non-Food'),
    ]  

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('fulfilled', 'Fulfilled'),
        ('expired', 'Expired'),
    ]

    DELIVERY_METHOD_CHOICES = [
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
        ('both', 'Both Available'),
    ]
    
    foodbank = models.ForeignKey(FoodBankProfile, on_delete=models.CASCADE, related_name='requests')
    original_request = models.ForeignKey(
        'RequestManagement',  # ← This is your recipient request model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='foodbank_request_created'  # One recipient request → one foodbank request
    )
    
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPE_CHOICES, default='food')
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    quantity_needed = models.PositiveIntegerField(blank=True, null=True)
    quantity_fulfilled = models.PositiveIntegerField(default=0)
    quantity_unit = models.CharField(max_length=20, choices=QUANTITY_UNITS, blank=True, null=True)
    custom_unit = models.CharField(max_length=50, blank=True, null=True, help_text="Custom unit when 'Other' is selected")
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHOD_CHOICES, blank=True, null=True)
    #linked_recipient_request = models.ForeignKey(RecipientRequest, on_delete=models.SET_NULL, null=True, blank=True)
    linked_request_management = models.ForeignKey(
        'RequestManagement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donor_requests'
    )
    deadline = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def update_fulfillment(self, additional_quantity):
        """Update fulfillment when new donation is received"""
        self.quantity_fulfilled += additional_quantity
        self.save()    
    
    def __str__(self):
        return f"{self.foodbank.foodbank_name} - {self.title}"
    
    def get_donation_response_status(self):
        """Get the status of donation responses for this request"""
        # Check if there are any donations for this request
        donations = self.donations.all()
        
        if not donations.exists():
            return 'sent_to_donors'  # Request sent but no donations yet
        
        # Check if there are pending donations
        pending_count = donations.filter(status='pending').count()
        if pending_count > 0:
            return 'awaiting_response'  # Foodbank needs to respond
        
        # Check if all donations are declined
        declined_count = donations.filter(status='declined').count()
        accepted_count = donations.filter(status='accepted').count()

        if declined_count > 0 and accepted_count == 0:
            return 'declined'  # All donations declined

        if accepted_count > 0:
            return 'accepted'  # At least one donation accepted

        return 'sent_to_donors'  # Default

    def get_foodbank_requests_status_label(self):
        donations = self.donations.all()
        if not donations.exists():
            return 'Sent to Donors'

        if donations.filter(status='accepted').exists():
            if self.is_partially_fulfilled():
                return 'Partially Fulfilled'
            return 'Fulfilled'

        if donations.filter(status='pending').exists():
            return 'Donation Made'

        if donations.filter(status='declined').exists():
            return 'Declined'

        return 'Sent to Donors'

    def get_requested_quantity_display(self):
        if not self.quantity_needed:
            return None
        unit_label = None
        if self.quantity_unit == 'other' and self.custom_unit:
            unit_label = self.custom_unit
        elif self.quantity_unit:
            try:
                unit_label = self.get_quantity_unit_display()
            except Exception:
                unit_label = self.quantity_unit
        if unit_label:
            return f"{self.quantity_needed} {unit_label}"
        return str(self.quantity_needed)

    def get_fulfillment_qty_amount_display(self):
        """Return a multi-line summary of accepted donations versus requested quantity."""
        requested_qty = self.get_requested_quantity_display()
        if not requested_qty:
            return "-"

        accepted_item_qty = 0
        accepted_money_amount = Decimal('0')
        accepted_subsidized_price = Decimal('0')
        accepted_subsidized_market_price = Decimal('0')

        for donation in self.donations.all():
            if getattr(donation, 'status', None) != 'accepted':
                continue

            donation_type = getattr(donation, 'donation_type', None)
            if donation_type == 'item':
                qty = getattr(donation, 'quantity', None)
                if qty:
                    accepted_item_qty += int(qty)
            elif donation_type == 'money':
                amt = getattr(donation, 'amount', None)
                if amt is not None:
                    accepted_money_amount += Decimal(str(amt))
            elif donation_type == 'subsidized':
                price = getattr(donation, 'subsidized_price', None)
                if price is not None:
                    accepted_subsidized_price += Decimal(str(price))
                market = getattr(donation, 'subsidized_market_price', None)
                if market is not None:
                    accepted_subsidized_market_price += Decimal(str(market))

        lines = []

        if accepted_item_qty:
            unit_label = None
            if self.quantity_unit == 'other' and self.custom_unit:
                unit_label = self.custom_unit
            elif self.quantity_unit:
                try:
                    unit_label = self.get_quantity_unit_display()
                except Exception:
                    unit_label = self.quantity_unit
            if unit_label:
                lines.append(f"{accepted_item_qty} {unit_label} (of {requested_qty} requested)")
            else:
                lines.append(f"{accepted_item_qty} (of {requested_qty} requested)")

        if accepted_subsidized_price:
            if accepted_subsidized_market_price:
                lines.append(
                    f"KES {accepted_subsidized_price:,.2f} (Market KES {accepted_subsidized_market_price:,.2f}) (for {requested_qty} requested)"
                )
            else:
                lines.append(f"KES {accepted_subsidized_price:,.2f} (for {requested_qty} requested)")

        if accepted_money_amount:
            lines.append(f"KES {accepted_money_amount:,.2f} (for {requested_qty} requested)")

        if lines:
            return "\n".join(lines)

        return f"0 (of {requested_qty} requested)"
    
    def get_total_donations_received(self):
        """Get total quantity/amount donated to this request (item + subsidized for quantity, money for amount)."""
        from django.db.models import Sum, Q

        if self.quantity_needed and self.quantity_unit:
            # For item requests: sum item quantities + subsidized quantities (so stock badges show for both)
            item_donations = self.donations.filter(donation_type='item')
            if self.quantity_unit == 'other':
                custom_unit = (self.custom_unit or '').strip()
                if custom_unit:
                    item_donations = item_donations.filter(
                        Q(quantity_unit='other') | Q(quantity_unit__iexact=custom_unit)
                    )
            else:
                item_donations = item_donations.filter(quantity_unit__iexact=self.quantity_unit)

            total_item = item_donations.aggregate(total=Sum('quantity'))['total'] or 0
            total_subsidized = self.donations.filter(
                donation_type='subsidized'
            ).aggregate(total=Sum('subsidized_quantity'))['total'] or 0
            return (total_item or 0) + (total_subsidized or 0)
        else:
            # For money requests, sum amounts (so stock badges show for monetary donations)
            total_amount = self.donations.filter(
                donation_type='money'
            ).aggregate(total=Sum('amount'))['total'] or 0
            return total_amount
    
    def get_remaining_need(self):
        """Get remaining quantity/amount needed"""
        if self.quantity_needed:
            total_received = self.get_total_donations_received()
            return max(0, self.quantity_needed - total_received)
        return 0
    
    def get_fulfillment_percentage(self):
        """Get percentage of request fulfilled"""
        if not self.quantity_needed or self.quantity_needed == 0:
            return 0
        
        total_received = self.get_total_donations_received()
        percentage = (total_received / self.quantity_needed) * 100
        return min(100, percentage)  # Cap at 100%
    
    def is_partially_fulfilled(self):
        """Check if request has received some donations but not fully fulfilled"""
        percentage = self.get_fulfillment_percentage()
        return 0 < percentage < 100
    
    def is_overfulfilled(self):
        """Check if donations exceed the requested amount"""
        return self.get_fulfillment_percentage() > 100
    
    def get_stock_used(self):
        """Quantity already issued from this FoodBankRequest to recipients."""
        return int(self.linked_request_management.quantity_fulfilled if self.original_request else self.quantity_fulfilled or 0)

    def get_stock_remaining(self):
        """Remaining available stock for foodbank allocations."""
        used = self.get_stock_used()
        needed = self.quantity_needed or 0
        remaining = needed - used
        return remaining if remaining > 0 else 0

    @property
    def allocation_usage(self):
        """Tuple (used, capacity, remaining) derived from actual allocations."""
        used = sum((alloc.quantity or alloc.amount or 0) for alloc in self.donation_allocations.all())
        capacity = self.get_total_donations_received() or self.quantity_needed or 0
        if capacity and used > capacity:
            used = capacity
        remaining = max(0, capacity - used)
        return used, capacity, remaining

    def get_donation_count(self):
        """Get number of donations made to this request"""
        return self.donations.count()
    
    def get_unique_donors_count(self):
        """Get number of unique donors who contributed to this request"""
        return self.donations.values('donor').distinct().count()
    
    def get_fulfilling_donors(self):
        """Get list of donors who have fulfilled this request"""
        from django.db.models import Q
        # Get all accepted donations for this request
        donations = self.donations.filter(status='accepted').select_related('donor', 'donor__donor_profile')
        donors = []
        seen_donors = set()
        for donation in donations:
            if donation.donor and donation.donor.id not in seen_donors:
                seen_donors.add(donation.donor.id)
                # Try to get donor profile name, fallback to email
                if hasattr(donation.donor, 'donor_profile') and donation.donor.donor_profile:
                    donor_name = donation.donor.donor_profile.full_name or donation.donor.donor_profile.organization_name or donation.donor.email
                else:
                    donor_name = donation.donor.email
                donors.append({
                    'name': donor_name,
                    'email': donation.donor.email,
                    'donation_count': self.donations.filter(donor=donation.donor, status='accepted').count()
                })
        return donors
    
    def get_fulfilling_donors_count(self):
        """Get count of unique donors who fulfilled this request"""
        return len(self.get_fulfilling_donors())
    
    def get_fulfilling_donors_display(self):
        """Get a formatted string of donors who fulfilled the request"""
        donors = self.get_fulfilling_donors()
        if not donors:
            return "No donors yet"
        if len(donors) == 1:
            return donors[0]['name']
        elif len(donors) <= 3:
            return ", ".join([d['name'] for d in donors])
        else:
            return f"{donors[0]['name']} and {len(donors) - 1} other(s)"
    
    def should_auto_fulfill(self):
        """Check if request should be automatically marked as fulfilled"""
        return self.get_fulfillment_percentage() >= 100 and self.status == 'active'


class Testimonial(models.Model):
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    recipient = models.ForeignKey(RecipientProfile, on_delete=models.CASCADE, related_name='testimonials')
    message = models.TextField(help_text="Share your story and the impact of the help you received")
    impact_image = models.ImageField(
        upload_to='testimonials/impact/', 
        blank=True, 
        null=True,
        help_text="Upload a photo showing the impact of the help you received"
    )
    
    # Approval workflow
    approval_status = models.CharField(
        max_length=20, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='pending',
        help_text="Admin approval status"
    )
    reviewed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_testimonials',
        limit_choices_to={'user_type': 'ADMIN'}
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Display management
    is_featured = models.BooleanField(default=False, help_text="Feature this testimonial on the homepage")
    display_on_public = models.BooleanField(default=True, help_text="Display on public portal when approved")
    display_start_date = models.DateTimeField(null=True, blank=True, help_text="When to start displaying (leave blank for immediate)")
    display_end_date = models.DateTimeField(null=True, blank=True, help_text="When to stop displaying (leave blank for 1 week from approval)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        recipient_name = self.recipient.full_name if hasattr(self.recipient, 'full_name') else self.recipient.user.email
        return f"Testimonial by {recipient_name} - {self.approval_status}"
    
    def is_currently_displayed(self):
        """Check if testimonial should be displayed on public portal"""
        if self.approval_status != 'approved' or not self.display_on_public:
            return False
        
        now = timezone.now()
        
        # Check start date
        if self.display_start_date and now < self.display_start_date:
            return False
        
        # Check end date
        if self.display_end_date and now > self.display_end_date:
            return False
        
        return True
    
    def set_default_display_period(self):
        """Set default 1-week display period from approval"""
        if not self.display_start_date:
            self.display_start_date = timezone.now()
        if not self.display_end_date:
            self.display_end_date = self.display_start_date + timedelta(days=7)

class FoodbankTestimonial(models.Model):
    """Testimonials from food banks about donors and the platform"""
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    foodbank = models.ForeignKey('FoodbankProfile', on_delete=models.CASCADE, related_name='testimonials')
    message = models.TextField(help_text="Share your experience with donors and the platform")
    impact_image = models.ImageField(
        upload_to='testimonials/foodbank/', 
        blank=True, 
        null=True,
        help_text="Upload a photo showing the impact of donations received"
    )
    
    # Approval workflow
    approval_status = models.CharField(
        max_length=20, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='pending',
        help_text="Admin approval status"
    )
    reviewed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_foodbank_testimonials',
        limit_choices_to={'user_type': 'ADMIN'}
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Display management
    is_featured = models.BooleanField(default=False, help_text="Feature this testimonial on the homepage")
    display_on_public = models.BooleanField(default=True, help_text="Display on public portal when approved")
    display_start_date = models.DateTimeField(null=True, blank=True, help_text="When to start displaying (leave blank for immediate)")
    display_end_date = models.DateTimeField(null=True, blank=True, help_text="When to stop displaying (leave blank for 1 week from approval)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Foodbank Testimonial'
        verbose_name_plural = 'Foodbank Testimonials'
    
    def __str__(self):
        foodbank_name = self.foodbank.foodbank_name if hasattr(self.foodbank, 'foodbank_name') else self.foodbank.user.email
        return f"Testimonial by {foodbank_name} - {self.approval_status}"
    
    def is_currently_displayed(self):
        """Check if testimonial should be displayed on public portal"""
        if self.approval_status != 'approved' or not self.display_on_public:
            return False
        
        now = timezone.now()
        
        # Check start date
        if self.display_start_date and now < self.display_start_date:
            return False
        
        # Check end date
        if self.display_end_date and now > self.display_end_date:
            return False
        
        return True
    
    def set_default_display_period(self):
        """Set default 1-week display period from approval"""
        if not self.display_start_date:
            self.display_start_date = timezone.now()
        if not self.display_end_date:
            self.display_end_date = self.display_start_date + timedelta(days=7)


class DonorTestimonial(models.Model):
    """Testimonials from donors about their giving experience and platform"""
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    donor = models.ForeignKey('DonorProfile', on_delete=models.CASCADE, related_name='testimonials')
    message = models.TextField(help_text="Share your experience as a donor and the impact you've witnessed")
    public_website_url = models.URLField(blank=True, null=True)
    impact_image = models.ImageField(
        upload_to='testimonials/donor/', 
        blank=True, 
        null=True,
        help_text="Upload a photo related to your donation experience or impact witnessed"
    )
    
    # Approval workflow
    approval_status = models.CharField(
        max_length=20, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='pending',
        help_text="Admin approval status"
    )
    reviewed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_donor_testimonials',
        limit_choices_to={'user_type': 'ADMIN'}
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Display management
    is_featured = models.BooleanField(default=False, help_text="Feature this testimonial on the homepage")
    display_on_public = models.BooleanField(default=True, help_text="Display on public portal when approved")
    display_start_date = models.DateTimeField(null=True, blank=True, help_text="When to start displaying (leave blank for immediate)")
    display_end_date = models.DateTimeField(null=True, blank=True, help_text="When to stop displaying (leave blank for 1 week from approval)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Donor Testimonial'
        verbose_name_plural = 'Donor Testimonials'
    
    def __str__(self):
        donor_name = self.donor.full_name if hasattr(self.donor, 'full_name') else self.donor.user.email
        return f"Testimonial by {donor_name} - {self.approval_status}"
    
    def is_currently_displayed(self):
        """Check if testimonial should be displayed on public portal"""
        if self.approval_status != 'approved' or not self.display_on_public:
            return False
        
        now = timezone.now()
        
        # Check start date
        if self.display_start_date and now < self.display_start_date:
            return False
        
        # Check end date
        if self.display_end_date and now > self.display_end_date:
            return False
        
        return True
    
    def set_default_display_period(self):
        """Set default 1-week display period from approval"""
        if not self.display_start_date:
            self.display_start_date = timezone.now()
        if not self.display_end_date:
            self.display_end_date = self.display_start_date + timedelta(days=7)


class FoodBank(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Donation(models.Model):
    
    DONATION_TYPES = [
        ('item', 'Item'),
        ('money', 'Money'),
        ('subsidized', 'Subsidized Goods'),
        ('csr', 'CSR'),
        ('other', 'Other'),
    ]
    
    DONATION_CATEGORIES = [
        ('food', 'Food'),
        ('non_food', 'Non-Food'),
        ('monetary', 'Monetary'),
        ('csr', 'CSR'),
        ('other', 'Other'),
    ]
    
    CSR_SUBCATEGORY_CHOICES = [
    ('philanthropy', 'Philanthropy'),
    ('volunteerism', 'Volunteerism'),
    ('environmental', 'Environmental/Sustainability'),
    ('humanitarian', 'Humanitarianism'),
    ('other', 'Other'),
   ]
    
    DONATION_MODES = [
        ('free', 'Free Donation'),
        ('subsidized', 'Subsidized Rate'),
        ('csr', 'CSR Initiative'),
        ('discussion', 'Requires Discussion'),
    ]
    
    DELIVERY_METHODS = [
    ('pickup', 'Pickup'),
    ('dropoff', 'Dropoff'),
    ]
    
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending Pickup'),
        ('scheduled', 'Scheduled'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

  
    donor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Fixed reference to CustomUser
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPES)
    donation_category = models.CharField(max_length=20, choices=DONATION_CATEGORIES, default='food')
    donation_mode = models.CharField(max_length=20, choices=DONATION_MODES, default='free')
    donation_code = models.CharField(max_length=10, unique=True, blank=True, null=True, editable=False)
    foodbank = models.ForeignKey(FoodBankProfile, on_delete=models.CASCADE)
    # Link donation to specific request (nullable for general donations)
    foodbank_request = models.ForeignKey('FoodBankRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    
    # For 'other' type donations - discussion system
    other_description = models.TextField(blank=True, null=True, help_text="Description for 'other' type donations")
    requires_discussion = models.BooleanField(default=False, help_text="Whether this donation requires discussion with foodbank")
    discussion_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Discussion'),
        ('in_progress', 'Discussion In Progress'),
        ('agreed', 'Terms Agreed'),
        ('declined', 'Declined'),
    ], blank=True, null=True)
    item_name = models.CharField(max_length=255, blank=True)
    agreed_clause = models.TextField(blank=True, null=True, help_text="Agreed terms/clause for CSR and Other donations after discussion")
    quantity = models.PositiveIntegerField(null=True, blank=True)
    quantity_unit = models.CharField(max_length=50, blank=True, null=True, help_text="Unit label for quantity (e.g., boxes, kits)")
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    subsidized_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    subsidized_market_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Original market price before discount")
    subsidized_product_type = models.CharField(max_length=255, blank=True, null=True)
    subsidized_quantity = models.PositiveIntegerField(null=True, blank=True)
    subsidized_quantity_unit = models.CharField(max_length=50, blank=True, null=True, help_text="Unit label for subsidized quantity")
    subsidized_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    message = models.TextField(blank=True)
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS, blank=True, null=True)
    mpesa_phone = models.CharField(max_length=12, blank=True, null=True, help_text="M-Pesa phone number for monetary donations")
    pickup_time = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    csr_subcategory = models.CharField(max_length=20, choices=CSR_SUBCATEGORY_CHOICES, blank=True)
    csr_custom_subcategory = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Custom CSR subcategory label when 'Other' is selected"
    )
    csr_description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    decline_message = models.TextField(blank=True, null=True)
    donated_at = models.DateTimeField(auto_now_add=True)
    is_allocated = models.BooleanField(default=False)
    request_management = models.ForeignKey(
        'RequestManagement',  # <-- Use string instead of class
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='donations'
    )

    subsidized_responded_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,  # Use your user model if Recipient extends it
        blank=True,
        related_name='subsidized_donations',
        limit_choices_to={'user_type': 'RECIPIENT'}  # optional filter
    )
    accepted_by_recipient = models.ForeignKey(
        'RecipientProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_subsidized_donations'
    )
    declined_by_recipient = models.ForeignKey(
        'RecipientProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='declined_subsidized_donations'
    )
    
    #is_general_donation = models.BooleanField(default=False)  # random donations

    def clean(self):
        # Validation based on donation_type (ValidationError so ModelForm shows errors)
        if self.donation_type == 'item' and not self.item_name:
            raise ValidationError(_('Item name must be provided for item donations'))
        if self.donation_type == 'money' and not self.amount:
            raise ValidationError(_('Amount must be provided for money donations'))
        if self.donation_type == 'subsidized' and not self.subsidized_price:
            raise ValidationError(_('Subsidized price must be provided for subsidized goods donations'))

    def get_remaining_quantity(self):
        """Get remaining quantity for item donations. Exclude declined allocations so declined stock goes back to available."""
        if self.donation_type != 'item':
            return 0
        allocated = sum(
            allocation.quantity or 0
            for allocation in self.allocations.filter(declined_by_recipient=False)
        )
        return max(0, self.quantity - allocated)

    def get_recipient_name(self):
        """Get the recipient name associated with this donation"""
        # Check if donation is accepted by a specific recipient (for subsidized donations)
        if self.accepted_by_recipient:
            return self.accepted_by_recipient.full_name
        
        # Check if donation is allocated to recipients
        allocations = self.allocations.all()
        if allocations.exists():
            if allocations.count() == 1:
                return allocations.first().recipient.full_name
            else:
                # Multiple recipients - show count
                return f"{allocations.count()} recipients"
        
        # Check if donation is linked to a foodbank request with original recipient
        if self.foodbank_request and hasattr(self.foodbank_request, 'original_request') and self.foodbank_request.original_request:
            return self.foodbank_request.original_request.recipient.full_name
        
        # No specific recipient linked
        return "Not allocated"

    def get_remaining_amount(self):
        """Get remaining amount for money/subsidized donations. Exclude declined allocations."""
        if self.donation_type not in ['money', 'subsidized']:
            return 0
        allocated = sum(
            float(allocation.amount or 0)
            for allocation in self.allocations.filter(declined_by_recipient=False)
        )
        max_amount = float(self.amount if self.donation_type == 'money' else (self.subsidized_price or 0))
        return max(0, max_amount - allocated)

    def get_remaining_subsidized_quantity(self):
        """Get remaining quantity (pieces) for subsidized donations. Exclude declined allocations."""
        if self.donation_type != 'subsidized':
            return 0
        total_qty = self.subsidized_quantity or self.quantity or 0
        allocated = sum(
            allocation.quantity or 0
            for allocation in self.allocations.filter(declined_by_recipient=False)
        )
        return max(0, total_qty - allocated)

    def is_fully_allocated(self):
        """Check if donation is fully allocated"""
        if self.donation_type == 'item':
            return self.get_remaining_quantity() == 0
        else:
            return self.get_remaining_amount() == 0
    
    def is_request_donation(self):
        """Check if this donation was made in response to a specific request"""
        return self.foodbank_request is not None
    
    def is_general_donation(self):
        """Check if this is a general donation (not tied to a specific request)"""
        return self.foodbank_request is None
    
    
    def get_donation_display(self):
        """Get a human-readable display of the donation"""
        if self.donation_type == 'item':
            return f"{self.quantity} {self.quantity_unit} of {self.item_name}"
        elif self.donation_type == 'money':
            return f"KES {self.amount:,.2f}"
        elif self.donation_type == 'subsidized':
            return f"Subsidized goods worth KES {self.subsidized_price:,.2f}"
        return "Unknown donation type"
    
    def calculate_subsidized_price(self):
        """Calculate the subsidized price based on market price and discount percentage"""
        if self.subsidized_market_price and self.subsidized_discount_percentage:
            discount_amount = (self.subsidized_market_price * self.subsidized_discount_percentage) / 100
            return self.subsidized_market_price - discount_amount
        return self.subsidized_price

    @property
    def subsidized_initial_amount(self):
        """Return the initial (market) amount for subsidized goods."""
        return self.subsidized_market_price or self.subsidized_price

    @property
    def subsidized_subsidy_amount(self):
        """Return the amount discounted from the initial market price."""
        if self.subsidized_market_price and self.subsidized_price:
            diff = self.subsidized_market_price - self.subsidized_price
            return diff if diff > Decimal('0') else None
        return None

    def get_estimated_impact(self):
        """Estimate the number of people this donation could help"""
        # Rough estimates - can be refined based on actual data
        if self.donation_type == 'item' and self.quantity:
            # Assume 1kg of food can provide 1 meal, 1 meal serves 1 person
            if self.quantity_unit in ['kg', 'kilograms']:
                return self.quantity
            elif self.quantity_unit in ['bags', 'packets']:
                return self.quantity * 5  # Assume each bag/packet is ~5kg
            elif self.quantity_unit in ['items', 'pieces']:
                return self.quantity * 2  # Assume each item serves 2 people
        elif self.donation_type == 'money' and self.amount:
            # Assume KES 100 can provide 1 meal
            return int(self.amount / 100)
        elif self.donation_type == 'subsidized' and self.subsidized_price:
            # Assume subsidized goods are 50% more efficient
            return int((self.subsidized_price / 100) * 1.5)
        return 0
    
    
    def contributes_to_request_fulfillment(self):
        """Check if this donation contributes to fulfilling its associated request"""
        if not self.foodbank_request:
            return False
        
        if self.donation_type == 'item' and self.foodbank_request.quantity_needed:
            return (self.item_name.lower() in self.foodbank_request.title.lower() or
                    self.quantity_unit == self.foodbank_request.quantity_unit)
        elif self.donation_type == 'money':
            return True  # Money donations are always useful
        
        return False

    def save(self, *args, **kwargs):
        # Money donations linked to a request should use the request's category (food/non_food), not 'monetary'
        if self.donation_type == 'money' and self.donation_category == 'monetary' and self.foodbank_request_id:
            try:
                fb_req = self.foodbank_request
                req_type = getattr(getattr(fb_req, 'original_request', None), 'request_type', None) or getattr(fb_req, 'donation_type', None)
                if req_type in ('food', 'non_food'):
                    self.donation_category = 'monetary'
            except Exception:
                pass
        creating = self.pk is None
        super().save(*args, **kwargs)
        if (creating or not self.donation_code) and self.pk:
            code = f"DN{self.pk:04d}"
            if self.donation_code != code:
                Donation.objects.filter(pk=self.pk).update(donation_code=code)
                self.donation_code = code

    def __str__(self):
        code = f" ({self.donation_code})" if self.donation_code else ""
        return f"{self.donor.email} - {self.donation_type}{code}"  # Fixed donor reference

class DonationDiscussion(models.Model):
    """Model for handling discussions between donors and foodbanks for 'other' type donations"""
    donation = models.OneToOneField(Donation, on_delete=models.CASCADE, related_name='discussion')
    donor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='donor_discussions')
    foodbank = models.ForeignKey('FoodBankProfile', on_delete=models.CASCADE, related_name='foodbank_discussions')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Response'),
        ('in_progress', 'Discussion In Progress'),
        ('agreed', 'Terms Agreed'),
        ('declined', 'Declined'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Discussion for {self.donation} - {self.status}"

class DonationDiscussionMessage(models.Model):
    """Messages within a donation discussion"""
    discussion = models.ForeignKey(DonationDiscussion, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['sent_at']
    
    def __str__(self):
        return f"Message from {self.sender.email} at {self.sent_at}"
    
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('acknowledgement', 'Acknowledgement'),
        ('request', 'New Request'),
        ('system', 'System Update'),
        ('donation_received', 'Donation Received'),
        ('request_fulfilled', 'Request Fulfilled'),
        ('urgent_request', 'Urgent Request'),
        ('donation_pickup', 'Donation Pickup'),
        ('donation_delivered', 'Donation Delivered'),
        ('system_maintenance', 'System Maintenance'),
        ('new_donor', 'New Donor'),
        ('request_expiring', 'Request Expiring'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} for {self.user.email}"
    
    @classmethod
    def create_notification(cls, user, notification_type, message, related_object=None):
        """Helper method to create notifications with optional related object"""
        notification = cls.objects.create(
            user=user,
            notification_type=notification_type,
            message=message,
            related_object_id=related_object.id if related_object else None,
            related_object_type=related_object.__class__.__name__ if related_object else None
        )
        return notification 

class DonationAllocation(models.Model):
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='allocations')
    recipient = models.ForeignKey('RecipientProfile', on_delete=models.CASCADE, related_name='allocations')
    request_management = models.ForeignKey(
        'RequestManagement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donation_allocations'
    )
    quantity = models.PositiveIntegerField(null=True, blank=True)  # For item donations
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # For money/subsidized
    allocated_at = models.DateTimeField(auto_now_add=True)
    is_acknowledged = models.BooleanField(default=False)
    declined_by_recipient = models.BooleanField(default=False, help_text="True when recipient declined this allocation (row stays visible with Declined status)")

    def __str__(self):
        donation_type = self.donation.get_donation_type_display()
        return f"{self.recipient.full_name} allocated {self.quantity or self.amount} from {donation_type} donation"


class UnspecifiedDonationManagement(models.Model):
    """Track unspecified/general donations through the approval workflow."""
    
    FOODBANK_STATUS_CHOICES = [
        ('pending_foodbank', 'Pending Foodbank Review'),
        ('accepted_by_foodbank', 'Accepted by Foodbank'),
        ('declined_by_foodbank', 'Declined by Foodbank'),
    ]
    
    RECIPIENT_STATUS_CHOICES = [
        ('not_applicable', 'Not Claimed'),
        ('pending_recipient', 'Available for Recipients'),
        ('accepted_by_recipient', 'Accepted by Recipient'),
        ('declined_by_recipient', 'Declined by Recipient'),
        ('received', 'Received by Recipient'),
    ]
    
    donation = models.OneToOneField(Donation, on_delete=models.CASCADE, related_name='unspecified_management')
    foodbank_status = models.CharField(max_length=30, choices=FOODBANK_STATUS_CHOICES, default='pending_foodbank')
    foodbank_reviewed_at = models.DateTimeField(null=True, blank=True)
    foodbank_decline_reason = models.TextField(blank=True, null=True)
    recipient_status = models.CharField(max_length=30, choices=RECIPIENT_STATUS_CHOICES, default='not_applicable')
    accepted_by_recipient = models.ForeignKey('RecipientProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_unspecified_donations')
    recipient_accepted_at = models.DateTimeField(null=True, blank=True)
    recipient_decline_reason = models.TextField(blank=True, null=True)
    received_at = models.DateTimeField(null=True, blank=True)
    recipient_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Unspecified Donation Management'
        verbose_name_plural = 'Unspecified Donation Management'
    
    def __str__(self):
        return f"Unspecified: {self.donation} - FB:{self.foodbank_status} / R:{self.recipient_status}"

    @property
    def category_display(self):
        """Label for Category column: CSR when donation is CSR type, else donation category/type."""
        d = self.donation
        if getattr(d, 'donation_type', None) == 'csr':
            return 'CSR'
        if getattr(d, 'donation_category', None) == 'csr':
            return 'CSR'
        if getattr(d, 'donation_mode', None) == 'csr':
            return 'CSR'
        try:
            if getattr(d, 'get_donation_type_display', None) and d.get_donation_type_display() == 'CSR':
                return 'CSR'
        except Exception:
            pass
        try:
            return d.get_donation_category_display() or d.get_donation_type_display() or '—'
        except Exception:
            return '—'
    
    def foodbank_accept(self):
        from django.utils import timezone
        self.foodbank_status = 'accepted_by_foodbank'
        self.foodbank_reviewed_at = timezone.now()
        self.recipient_status = 'pending_recipient'
        self.save()
    
    def foodbank_decline(self, reason=None):
        from django.utils import timezone
        self.foodbank_status = 'declined_by_foodbank'
        self.foodbank_reviewed_at = timezone.now()
        if reason:
            self.foodbank_decline_reason = reason
        self.save()
    
    def recipient_accept(self, recipient_profile, notes=None):
        from django.utils import timezone
        self.recipient_status = 'accepted_by_recipient'
        self.accepted_by_recipient = recipient_profile
        self.recipient_accepted_at = timezone.now()
        if notes:
            self.recipient_notes = notes
        self.save()
    
    def confirm_received(self, notes=None):
        from django.utils import timezone
        self.recipient_status = 'received'
        self.received_at = timezone.now()
        if notes:
            self.recipient_notes = notes
        self.save()
    
    def get_foodbank_status_badge_class(self):
        status_classes = {
            'pending_foodbank': 'bg-warning',
            'accepted_by_foodbank': 'bg-success',
            'declined_by_foodbank': 'bg-danger',
        }
        return status_classes.get(self.foodbank_status, 'bg-secondary')
    
    def get_recipient_status_badge_class(self):
        status_classes = {
            'not_applicable': 'bg-secondary',
            'pending_recipient': 'bg-info',
            'accepted_by_recipient': 'bg-primary',
            'declined_by_recipient': 'bg-danger',
            'received': 'bg-success',
        }
        return status_classes.get(self.recipient_status, 'bg-secondary')


class PaymentTransaction(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    ]
    
    donation = models.OneToOneField(Donation, on_delete=models.CASCADE, related_name='payment_transaction')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    mpesa_checkout_request_id = models.CharField(max_length=255, blank=True, null=True)
    mpesa_merchant_request_id = models.CharField(max_length=255, blank=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=255, blank=True, null=True, unique=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='credit_card')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stripe_response = models.JSONField(blank=True, null=True)  # Store full Stripe response
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - {self.donation.donor.email} - {self.amount} {self.currency}"
    
    def calculate_net_amount(self):
        """Calculate net amount after transaction fees"""
        self.net_amount = self.amount - self.transaction_fee
        return self.net_amount
    
    def mark_completed(self):
        """Mark payment as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self):
        """Mark payment as failed"""
        self.status = 'failed'
        self.save() 


class RequestManagement(models.Model):
    """Unified model for managing requests between recipients and foodbanks"""
    
    REQUEST_TYPE_CHOICES = [
        ('food', 'Food'),
        ('non_food', 'Non-Food'),
    ]
    
    REQUEST_CATEGORY_CHOICES = [
        ('food', 'Food'),
        ('non_food', 'Non-Food'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned to Foodbank'),  # new status
        ('awaiting_recipient', 'Awaiting Recipient'),  # After foodbank accepts donation
        ('fulfilled', 'Fulfilled'),
        ('partial', 'Partially Fulfilled'),
        ('acknowledged', 'Acknowledged by Recipient'),
        ('submitted', 'Submitted to Donors - Awaiting Donation'),
        ('donation_received', 'Donated awaiting approval'),
        ('declined', 'Declined'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
        ('both', 'Both Available'),
    ]
    
    # Core request information
    recipient = models.ForeignKey(RecipientProfile, on_delete=models.CASCADE, related_name='managed_requests')
    foodbank = models.ForeignKey(
        FoodBankProfile, 
        on_delete=models.CASCADE, 
        null=True,          # ← ADD THIS
        blank=True,         # ← ADD THIS
        related_name='managed_requests'
    )
    
    # Request details
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    request_category = models.CharField(max_length=20, choices=REQUEST_CATEGORY_CHOICES, blank=True, null=True)
    description = models.TextField(help_text="e.g., '100 bags of maize'")
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=20, choices=QUANTITY_UNITS)
    custom_unit = models.CharField(max_length=50, blank=True, null=True, help_text="Custom unit when 'Other' is selected")
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHOD_CHOICES)
    location = models.CharField(max_length=255, help_text="Delivery/pickup location")
    acknowledged_by_recipient = models.BooleanField(default=False)
    awaiting_donors = models.BooleanField(default=False)
    
    # Status and notes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    additional_notes = models.TextField(blank=True, null=True, help_text="Notes added by foodbank")
    
    # Timestamps
    time_of_request = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fulfilled_at = models.DateTimeField(blank=True, null=True)
    quantity_fulfilled = models.PositiveIntegerField(default=0)
    decline_message = models.TextField(blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    assigned_foodbank = models.ForeignKey(
        FoodBankProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests',
        help_text="Foodbank that accepted the anonymous request"
    )
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, null=True, blank=True)
    foodbank_request = models.ForeignKey(
        'FoodBankRequest', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='recipient_requests'
    )
    
    # Tracking fields
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_requests')
    
    class Meta:
        ordering = ['-time_of_request']
        verbose_name = 'Request Management'
        verbose_name_plural = 'Request Management'
    
    def __str__(self):
        return f"{self.recipient.full_name} → {self.foodbank.foodbank_name}: {self.description}"
    
    def save(self, *args, **kwargs):
        if self.quantity > 0:
            fulfilled = self.quantity_fulfilled or 0
            needed = self.quantity

            if fulfilled >= needed:
                if self.status not in ['awaiting_recipient', 'declined']:
                    self.status = 'fulfilled'
                if not self.fulfilled_at:
                    self.fulfilled_at = timezone.now()
            elif fulfilled > 0:
                protected_statuses = {'submitted', 'donation_received', 'awaiting_recipient', 'declined'}
                if self.status not in protected_statuses:
                    self.status = 'partial'
        super().save(*args, **kwargs)

    
    @property
    def foodbank_name(self):
        """Get foodbank name for display"""
        if self.foodbank:
            return self.foodbank.foodbank_name
        elif self.is_anonymous and self.assigned_foodbank:
            return self.assigned_foodbank.foodbank_name
        else:
            return "Anonymous Request"
    
    @property
    def recipient_name(self):
        """Get recipient name for display"""
        return self.recipient.full_name

        
    
    def get_remaining_quantity(self):
        """Get remaining quantity to be fulfilled"""
        return max(0, self.quantity - self.quantity_fulfilled)

    def get_donation_quantity_context(self):
        """Quantity figure to pair with monetary/subsidized donations in UI."""
        remaining = self.get_remaining_quantity()
        if remaining > 0:
            return remaining
        return self.quantity
    
    def mark_fulfilled(self, user=None, notes=None):
        """Mark request as fulfilled"""
        from django.utils import timezone
        self.status = 'fulfilled'
        self.fulfilled_at = timezone.now()
        if user:
            self.updated_by = user
        if notes:
            self.additional_notes = notes
        self.save()
    
    def mark_denied(self, user=None, notes=None):
        """Mark request as denied"""
        self.status = 'denied'
        if user:
            self.updated_by = user
        if notes:
            self.additional_notes = notes
        self.save()
    
    def mark_partial(self, user=None, notes=None):
        """Mark request as partially fulfilled"""
        self.status = 'partial'
        if user:
            self.updated_by = user
        if notes:
            self.additional_notes = notes
        self.save()
    def get_display_status(self):
        """
        Returns the exact status text shown in the recipient table
        """
        if self.status == 'partial':
            if self.additional_notes and "Receipt Confirmed" in self.additional_notes:
                return "Partially Fulfilled – Received"
            elif self.acknowledged_by_recipient:
                return "Partially Fulfilled – Acknowledged"
            return "Partially Fulfilled"

        if self.status == 'fulfilled':
            if self.additional_notes and "Receipt Confirmed" in self.additional_notes:
                return "Fulfilled-Received"
            elif self.acknowledged_by_recipient:
                return "Fulfilled-Acknowledged"
            return "Fulfilled"

        if self.status == 'awaiting_recipient':
            return "Awaiting Your Response"

        if self.status == 'donation_received':
            return "Donated - Awaiting Approval"

        if self.status == 'submitted':
            return "Submitted to Donors - Awaiting Donation"

        if self.status == 'declined':
            return "Declined"

        return "Pending"

    def was_declined_by_foodbank(self):
        """Identify foodbank-driven declines so we can mask them from recipients."""
        if self.status != 'declined':
            return False

        updater = getattr(self, 'updated_by', None)
        if not updater:
            return False

        user_type = getattr(updater, 'user_type', '') or ''
        return user_type.upper() == 'FOODBANK'

    @property
    def has_donations(self):
        """Check if this request already has donations tied to it."""
        if self.donation_id:
            return True

        # Direct FK to FoodBankRequest if populated
        fb_request = getattr(self, 'foodbank_request', None)
        if fb_request and fb_request.donations.exists():
            return True

        # Some templates access reverse relation foodbank_request_created
        fb_request_rel = getattr(self, 'foodbank_request_created', None)
        if fb_request_rel is not None:
            if hasattr(fb_request_rel, 'all'):
                fb_request = fb_request_rel.first()
            else:
                fb_request = fb_request_rel

            if fb_request and fb_request.donations.exists():
                return True

        return False

    @property
    def foodbank_declined_donation(self):
        """True when a foodbank declined after at least one donor contributed."""
        return self.was_declined_by_foodbank() and self.has_donations

    @property
    def foodbank_declined_request(self):
        """True when a foodbank directly declined the recipient request (no donors)."""
        return self.was_declined_by_foodbank() and not self.has_donations

    @property
    def recipient_declined_request(self):
        """Identify requests declined by the recipient so foodbanks can tell."""
        if self.status != 'declined':
            return False
        updater = getattr(self, 'updated_by', None)
        if not updater:
            return False
        return (getattr(updater, 'user_type', '') or '').upper() == 'RECIPIENT'

    def get_recipient_display_status(self):
        """Status label recipients should see (hides foodbank-declined donations)."""
        if self.foodbank_declined_donation:
            return "Pending"
        return self.get_display_status()

    def get_status_badge_class(self):
        """Get Bootstrap badge class for status"""
        status_classes = {
            'pending': 'bg-warning',
            'awaiting_recipient': 'bg-info',
            'fulfilled': 'bg-success',
            'denied': 'bg-danger',
            'partial': 'bg-info',
            'donation_received': 'bg-primary',
            'acknowledged': 'bg-success',
            'declined': 'bg-danger',
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_type_badge_class(self):
        """Get Bootstrap badge class for request type"""
        type_classes = {
            'food': 'bg-primary',
            'non_food': 'bg-secondary',
        }
        return type_classes.get(self.request_type, 'bg-secondary')
    
    def is_overdue(self):
        """Check if request is overdue (pending for more than 7 days)"""
        if self.status != 'pending':
            return False
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() - self.time_of_request > timedelta(days=7)
    # In your existing RequestManagement model, add this method:
    def is_subsidized_response(self):
        """Check if this request is a response to a subsidized donation"""
        return 'subsidized' in self.description.lower() or self.request_type == 'subsidized'

    # Add a field to link to the original subsidized donation (optional)
    # original_subsidized_donation = models.ForeignKey(Donation, on_delete=models.SET_NULL, null=True, blank=True)


class SupportMessage(models.Model):
    """Model to store support messages from users"""
    SUBJECT_CHOICES = [
        # Donor subjects
        ('donation_help', 'Help with Donation Process'),
        ('payment_issue', 'Payment or Transaction Issues'),
        ('tax_receipt', 'Tax Receipt Questions'),
        
        # Foodbank subjects
        ('request_management', 'Help with Request Management'),
        ('donation_processing', 'Donation Processing Issues'),
        ('analytics_reports', 'Analytics and Reports'),
        ('account_setup', 'Account Setup and Configuration'),
        ('recipient_communication', 'Recipient Communication'),
        ('training_resources', 'Training and Resources'),
        
        # Recipient subjects
        ('request_help', 'Help with My Request'),
        ('donation_inquiry', 'Donation Inquiry'),
        
        # Common subjects
        ('account_issue', 'Account Issues'),
        ('technical_support', 'Technical Support'),
        ('feedback', 'Feedback or Suggestions'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='support_messages')
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    admin_response = models.TextField(blank=True, null=True)
    assigned_to = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_support_messages',
        limit_choices_to={'is_staff': True}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Support Message'
        verbose_name_plural = 'Support Messages'
    
    def __str__(self):
        return f"{self.user.email} - {self.get_subject_display()} ({self.status})"
    
    def get_user_type_display(self):
        """Get user type for display"""
        return self.user.get_user_type_display()
    
    def mark_resolved(self):
        """Mark message as resolved"""
        from django.utils import timezone
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()
    
    def get_priority_badge_class(self):
        """Get Bootstrap badge class for priority"""
        priority_classes = {
            'low': 'bg-secondary',
            'medium': 'bg-info',
            'high': 'bg-warning',
            'urgent': 'bg-danger',
        }
        return priority_classes.get(self.priority, 'bg-secondary')
    
    def get_status_badge_class(self):
        """Get Bootstrap badge class for status"""
        status_classes = {
            'new': 'bg-primary',
            'in_progress': 'bg-warning',
            'resolved': 'bg-success',
            'closed': 'bg-secondary',
        }
        return status_classes.get(self.status, 'bg-secondary')


class SupportMessageReply(models.Model):
    support_message = models.ForeignKey(SupportMessage, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_message_replies')
    message = models.TextField()
    is_from_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class FoodBankSubscription(models.Model):
    """Subscription model for food banks with 3-month free trial"""
    PLAN_CHOICES = [
        ('trial', 'Free Trial (3 Months)'),
        ('monthly', 'Monthly Plan (KSH 2,000)'),
        ('yearly', 'Yearly Plan (KSH 10,000)'),
    ]
    
    STATUS_CHOICES = [
        ('trial', 'Trial Period'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    ]
    
    foodbank = models.OneToOneField(FoodBankProfile, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='trial')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    
    # Trial period tracking
    trial_start_date = models.DateTimeField(auto_now_add=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    
    # Subscription period tracking
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Food Bank Subscription'
        verbose_name_plural = 'Food Bank Subscriptions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.foodbank.foodbank_name} - {self.get_plan_display()} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-set trial end date to 3 months from start if not set
        if not self.trial_end_date and self.trial_start_date:
            self.trial_end_date = self.trial_start_date + timedelta(days=90)
        super().save(*args, **kwargs)
    
    def is_trial_active(self):
        """Check if trial period is still active"""
        if self.status != 'trial':
            return False
        if not self.trial_end_date:
            return False
        return timezone.now() < self.trial_end_date
    
    def is_subscription_active(self):
        """Check if paid subscription is active"""
        if self.status != 'active':
            return False
        if not self.subscription_end_date:
            return False
        return timezone.now() < self.subscription_end_date
    
    def can_access_features(self):
        """Check if food bank can access platform features"""
        return self.is_trial_active() or self.is_subscription_active()
    
    def days_remaining(self):
        """Get days remaining in current period"""
        if self.status == 'trial' and self.trial_end_date:
            delta = self.trial_end_date - timezone.now()
            return max(0, delta.days)
        elif self.status == 'active' and self.subscription_end_date:
            delta = self.subscription_end_date - timezone.now()
            return max(0, delta.days)
        return 0
    
    def get_plan_price(self):
        """Get the price for current plan"""
        if self.plan == 'monthly':
            return 2000
        elif self.plan == 'yearly':
            return 10000
        return 0
    
    def extend_subscription(self, plan_type):
        """Extend subscription based on plan type"""
        from django.utils import timezone
        
        if plan_type == 'monthly':
            duration = timedelta(days=30)
            self.plan = 'monthly'
        elif plan_type == 'yearly':
            duration = timedelta(days=365)
            self.plan = 'yearly'
        else:
            return False
        
        # If currently in trial or expired, start from now
        if self.status in ['trial', 'expired']:
            self.subscription_start_date = timezone.now()
            self.subscription_end_date = self.subscription_start_date + duration
        # If active, extend from current end date
        elif self.status == 'active' and self.subscription_end_date:
            self.subscription_end_date = self.subscription_end_date + duration
        else:
            self.subscription_start_date = timezone.now()
            self.subscription_end_date = self.subscription_start_date + duration
        
        self.status = 'active'
        self.save()
        return True


class SubscriptionPayment(models.Model):
    """Payment evidence submission for subscription verification"""
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('requires_info', 'Requires More Information'),
    ]
    
    PLAN_CHOICES = [
        ('monthly', 'Monthly Plan (KSH 2,000)'),
        ('yearly', 'Yearly Plan (KSH 10,000)'),
    ]
    
    subscription = models.ForeignKey(FoodBankSubscription, on_delete=models.CASCADE, related_name='payments')
    foodbank = models.ForeignKey(FoodBankProfile, on_delete=models.CASCADE, related_name='subscription_payments')
    
    # Payment details
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_reference = models.CharField(max_length=100, help_text="M-Pesa code or bank reference number")
    payment_date = models.DateField()
    payment_evidence = models.ImageField(upload_to='subscription_payments/', help_text="Upload screenshot of payment confirmation")
    notes = models.TextField(blank=True, null=True, help_text="Any additional information about the payment")
    
    # Admin verification fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    verified_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes for admin")
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection (shown to food bank)")
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Subscription Payment'
        verbose_name_plural = 'Subscription Payments'
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.foodbank.foodbank_name} - {self.get_plan_type_display()} - {self.get_status_display()}"
    
    def approve_payment(self, admin_user):

        """Approve payment and activate subscription"""
        from django.utils import timezone
        
        # Extend the subscription first to check if it succeeds
        if not self.subscription.extend_subscription(self.plan_type):
            return False
        
        self.status = 'approved'
        self.verified_by = admin_user
        self.verified_at = timezone.now()
        self.save()
        
        # Create notification for food bank
        Notification.create_notification(
            user=self.foodbank.user,
            notification_type='system',
            message=f'Your {self.get_plan_type_display()} payment has been approved! Your subscription is now active.',
            related_object=self
        )
        
        return True
    
    def reject_payment(self, admin_user, reason):
        """Reject payment submission"""
        from django.utils import timezone
        
        self.status = 'rejected'
        self.verified_by = admin_user
        self.verified_at = timezone.now()
        self.rejection_reason = reason
        self.save()
        
        # Create notification for food bank
        Notification.create_notification(
            user=self.foodbank.user,
            notification_type='system',
            message=f'Your subscription payment was not approved. Reason: {reason}',
            related_object=self
        )
        
        return True
    
    def get_status_badge_class(self):
        """Get Bootstrap badge class for status"""
        status_classes = {
            'pending': 'bg-warning',
            'approved': 'bg-success',
            'rejected': 'bg-danger',
            'requires_info': 'bg-info',
        }
        return status_classes.get(self.status, 'bg-secondary')


class Subscription(models.Model):
    USER_TYPE_CHOICES = [
        ('donor', 'Donor'),
        ('foodbank', 'Foodbank'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    is_active = models.BooleanField(default=False)
    start_date = models.DateTimeField(default=now)
    end_date = models.DateTimeField(null=True, blank=True)
    payment_status = models.CharField(max_length=20, default='unpaid')
    last_payment_date = models.DateTimeField(null=True, blank=True)

    def is_subscription_valid(self):
        """Check if the subscription is still valid."""
        if self.end_date and self.end_date > now():
            return True
        return False

    def __str__(self):
        return f"{self.user.username} - {self.user_type} - {'Active' if self.is_active else 'Inactive'}"


class AdminLoginLog(models.Model):
    """Track admin login activities"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='login_logs')
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    session_key = models.CharField(max_length=40, blank=True, null=True)
    login_successful = models.BooleanField(default=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    session_duration = models.DurationField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Admin Login Log'
        verbose_name_plural = 'Admin Login Logs'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.email} - {self.login_time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def calculate_session_duration(self):
        """Calculate and update session duration"""
        if self.logout_time and self.login_time:
            self.session_duration = self.logout_time - self.login_time
            self.save()
            return self.session_duration
        return None
    
    def get_session_duration_display(self):
        """Get human-readable session duration"""
        if self.session_duration:
            total_seconds = int(self.session_duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "Active" if not self.logout_time else "Unknown"


class AdminCode(models.Model):
    """Admin registration codes managed by superadmin"""
    code = models.CharField(max_length=50, unique=True, help_text="Unique admin registration code")
    description = models.CharField(max_length=200, blank=True, help_text="Optional description for this code")
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_admin_codes')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text="Whether this code can be used for registration")
    used_count = models.PositiveIntegerField(default=0, help_text="Number of times this code has been used")
    last_used_at = models.DateTimeField(null=True, blank=True, help_text="When this code was last used")
    last_used_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_admin_codes')
    
    class Meta:
        verbose_name = 'Admin Registration Code'
        verbose_name_plural = 'Admin Registration Codes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} ({'Active' if self.is_active else 'Inactive'})"
    
    def mark_as_used(self, user):
        """Mark this code as used by a specific user"""
        from django.utils import timezone
        self.used_count += 1
        self.last_used_at = timezone.now()
        self.last_used_by = user
        self.save()
    
    def get_status_display(self):
        """Get human-readable status"""
        if not self.is_active:
            return "Inactive"
        elif self.used_count == 0:
            return "Unused"
        else:
            return f"Used {self.used_count} time{'s' if self.used_count != 1 else ''}"
        
from django.utils import timezone

class AccountDeletionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    processed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='processed_deletion_requests'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Deletion request for {self.user.email} - {self.status}"


class SystemSupportDonation(models.Model):
    """Model for tracking donations to support FoodBank Hub system operations"""
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        
    ]
    
    donor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='system_support_donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount donated in KES")
    payment_proof = models.ImageField(upload_to='system_support_payments/', help_text="Upload screenshot or proof of payment")
    transaction_reference = models.CharField(max_length=100, blank=True, null=True, help_text="M-Pesa code or bank reference (optional)")
    notes = models.TextField(blank=True, null=True, help_text="Any additional notes about the donation")
    
    # Verification fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_system_donations')
    verified_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal admin notes")
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection (shown to donor)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'System Support Donation'
        verbose_name_plural = 'System Support Donations'
    
    def __str__(self):
        return f"{self.donor.email} - KES {self.amount} ({self.get_status_display()})"
    
    def approve(self, admin_user, notes=None):
        """Approve the donation"""
        self.status = 'approved'
        self.verified_by = admin_user
        self.verified_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()
    
    def reject(self, admin_user, reason):
        """Reject the donation"""
        self.status = 'rejected'
        self.verified_by = admin_user
        self.verified_at = timezone.now()
        self.rejection_reason = reason
        self.save()

# models.py
class DonationResponse(models.Model):
    RESPONSE_CHOICES = [
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('partial', 'Partial'),
    ]
    
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='responses')
    recipient = models.ForeignKey(RecipientProfile, on_delete=models.CASCADE)
    response_type = models.CharField(max_length=20, choices=RESPONSE_CHOICES)
    partial_quantity = models.PositiveIntegerField(null=True, blank=True)
    responded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['donation', 'recipient']  # One response per recipient per donation


class NewsSection(models.Model):
    """Model for dynamic news/announcement section on landing page"""
    title = models.CharField(max_length=200, help_text="News title or headline")
    content = models.TextField(help_text="News content or description")
    image = models.ImageField(upload_to='news_section/', help_text="Upload graphic or image for the news")
    is_active = models.BooleanField(default=True, help_text="Display this news on the landing page")
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_news')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    display_order = models.IntegerField(default=0, help_text="Lower numbers appear first")
    
    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'News Section'
        verbose_name_plural = 'News Sections'
    
    def __str__(self):
        return f"{self.title} - {'Active' if self.is_active else 'Inactive'}"
