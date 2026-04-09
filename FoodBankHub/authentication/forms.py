from django import forms
from django.forms import DateTimeInput
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, DonorProfile, FoodBankProfile, RecipientProfile, Donation, FoodBankRequest, DonationAllocation, RecipientRequest, Testimonial, FoodbankTestimonial, DonorTestimonial, SubscriptionPayment, SystemSupportDonation, QUANTITY_UNITS
from django.contrib.auth import authenticate
from .validators import validate_strong_password, strong_password_validator, PasswordStrengthMeter

class CustomLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        
        'placeholder': 'Enter your email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password'
    }))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        
        super().__init__(*args, **kwargs)
        self.user_cache = None

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    'Please enter a correct email and password. Note that both fields may be case-sensitive.',
                    code='invalid_login',
                )
            else:
                from django.contrib.auth import get_user_model
                UserModel = get_user_model()
                if not self.user_cache.is_active:
                    raise forms.ValidationError('This account is inactive.', code='inactive')
        return self.cleaned_data

    def get_user(self):
        return self.user_cache

class BaseRegistrationForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your phone number'
    }))
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'password1',
            'data-toggle': 'password'
        }),
        help_text=strong_password_validator.get_help_text(),
        validators=[validate_strong_password]
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'id': 'password2'
        })
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'password1', 'password2')
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            # Validate password strength
            validate_strong_password(password1)
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError("Passwords don't match.")
            
            # Additional validation
            if len(password1) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            
            # Check for common patterns
            if password1.lower() in ['password', '123456', 'qwerty', 'admin']:
                raise ValidationError("This password is too common. Please choose a stronger password.")
        
        return cleaned_data

class DonorRegistrationForm(BaseRegistrationForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter first name'
    }))
    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter last name'
    }))
    location = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your location (City, Country)'
    }))
    is_organization = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'
    }))
    organization_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter organization name'
    }))

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + ('first_name', 'last_name', 'location', 'is_organization', 'organization_name')

    def clean_organization_name(self):
        is_organization = self.cleaned_data.get('is_organization')
        organization_name = self.cleaned_data.get('organization_name')
        
        if is_organization and not organization_name:
            raise forms.ValidationError('Organization name is required when registering as an organization.')
        
        return organization_name

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'DONOR'
        if commit:
            user.save()
            DonorProfile.objects.create(
                user=user,
                full_name=f"{self.cleaned_data['first_name']} {self.cleaned_data['last_name']}",
                location=self.cleaned_data.get('location', ''),
                is_organization=self.cleaned_data['is_organization'],
                organization_name=self.cleaned_data['organization_name'] if self.cleaned_data['is_organization'] else None
            )
        return user

class FoodBankRegistrationForm(BaseRegistrationForm):
    foodbank_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter foodbank name'
    }))
    contact_first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter contact first name'
    }))
    contact_last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter contact last name'
    }))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter address'
    }))
    service_type = forms.ChoiceField(
        choices=FoodBankProfile.SERVICE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text="What type of assistance does your food bank provide?"
    )
    authority_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'form-control'
    }))
    urgent_request_picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'form-control'
    }))
    additional_documents = forms.FileField(required=False, widget=forms.FileInput(attrs={
        'class': 'form-control',
        'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
    }))

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + ('foodbank_name', 'contact_first_name', 'contact_last_name', 'address', 'service_type', 'authority_picture', 'urgent_request_picture', 'additional_documents')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'FOODBANK'
        if commit:
            user.save()
            FoodBankProfile.objects.create(
                user=user,
                foodbank_name=self.cleaned_data['foodbank_name'],
                contact_person=f"{self.cleaned_data['contact_first_name']} {self.cleaned_data['contact_last_name']}",
                address=self.cleaned_data.get('address', ''),
                service_type=self.cleaned_data['service_type'],
                authority_picture=self.cleaned_data['authority_picture'],
                urgent_request_picture=self.cleaned_data['urgent_request_picture'],
                additional_documents=self.cleaned_data['additional_documents'],
                is_approved='pending'  # Set to pending by default
            )
        return user

class RecipientRegistrationForm(BaseRegistrationForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter first name'
    }))
    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter last name'
    }))
    location = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your location'
    }))
    is_organization = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'
    }))
    organization_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter organization name'
    }))
    consent_subsidized_goods = forms.BooleanField(
        required=False,
        label="I consent to receive goods at subsidized rates or for free",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta(BaseRegistrationForm.Meta):
        fields = BaseRegistrationForm.Meta.fields + (
            'first_name', 'last_name', 'location', 'is_organization', 'organization_name', 'consent_subsidized_goods'
        )
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'RECIPIENT'
        if commit:
            user.save()
            RecipientProfile.objects.create(
                user=user,
                full_name=f"{self.cleaned_data['first_name']} {self.cleaned_data['last_name']}",
                location=self.cleaned_data['location'],
                is_organization=self.cleaned_data['is_organization'],
                organization_name=self.cleaned_data['organization_name'] if self.cleaned_data['is_organization'] else None
            )
        return user 
    
    #Donation
class DonationForm(forms.ModelForm):
    
     # Optional: override fields for better UX
    #csr_subcategory = forms.ChoiceField(
        #choices=CSR_SUBCATEGORY_CHOICES,
        #required=False,
        #widget=forms.Select(attrs={'class': 'form-select'})
    #)
    csr_description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=False
    )
    csr_custom_subcategory = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter custom CSR type (e.g., STEM Scholarships)'
        })
    )
    # Make foodbank optional when donating to specific requests
    foodbank = forms.ModelChoiceField(
        queryset=FoodBankProfile.objects.all(),
        empty_label="Select a Food Bank",
        required=False,  # Make it optional for request-based donations
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_foodbank'
        })
    )
    
    # Add request field for context
    request_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Donation
        fields = [
            'donation_category', 'donation_mode', 'donation_type', 'foodbank', 'item_name', 'quantity', 
            'quantity_unit', 'amount', 'subsidized_price', 'subsidized_market_price', 'subsidized_product_type',
            'subsidized_quantity', 'subsidized_quantity_unit', 'other_description', 'mpesa_phone', 'csr_subcategory',
            'csr_description', 'csr_custom_subcategory',
            'message', 'delivery_method', 'pickup_time'
        ]
        widgets = {
            'donation_category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_donation_category'
            }),
            'donation_mode': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_donation_mode'
            }),
            'donation_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_donation_type'
            }),
            'item_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quantity',
                'min': '1'
            }),
            'quantity_unit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount in KES',
                'min': '0.01',
                'max': '9999999999999.99',
                'step': '0.01'
            }),
            'subsidized_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your subsidized price',
                'min': '0.01',
                'step': '0.01',
                'id': 'subsidized_price_input'
            }),
            'subsidized_market_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter market price in KES',
                'min': '0.01',
                'step': '0.01',
                'id': 'subsidized_market_price'
            }),
            'subsidized_product_type': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'subsidized_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quantity',
                'min': '1'
            }),
            'subsidized_quantity_unit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'other_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your donation in detail. What are you offering? What are the terms?'
            }),
            'mpesa_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '7XXXXXXXX',
                'pattern': '[7][0-9]{8}',
                'maxlength': '9'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional message to the food bank...'
            }),
            'delivery_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'pickup_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request_context = kwargs.pop('request_context', None)
        super().__init__(*args, **kwargs)
        
        # Set foodbank label
        self.fields['foodbank'].label_from_instance = lambda obj: obj.foodbank_name
        
        # If we have a request context, pre-fill foodbank and make it read-only
        if self.request_context and hasattr(self.request_context, 'foodbank'):
            self.fields['foodbank'].initial = self.request_context.foodbank
            self.fields['foodbank'].widget.attrs['readonly'] = True
            self.fields['foodbank'].widget.attrs['class'] = 'form-control bg-light'
            
            # Handle quantity_unit from request context
            if hasattr(self.request_context, 'quantity_unit') and self.request_context.quantity_unit:
                request_unit = self.request_context.quantity_unit.lower().strip()
                
                # Check if the request's quantity_unit matches any of our choices
                from .models import QUANTITY_UNITS
                valid_choices = [choice[0] for choice in QUANTITY_UNITS]
                
                if request_unit in valid_choices:
                    self.fields['quantity_unit'].initial = request_unit
                else:
                    # Try to map common variations to our choices
                    unit_mapping = {
                        'kilograms': 'kg',
                        'kilogram': 'kg',
                        'kgs': 'kg',
                        'liters': 'litres',
                        'liter': 'litres',
                        'l': 'litres',
                        'packet': 'packets',
                        'item': 'items',
                        'bag': 'bags',
                        'box': 'boxes',
                        'can': 'cans',
                        'bottle': 'bottles',
                        'piece': 'pieces',
                        'unit': 'units',
                        'ton': 'tons',
                        'gram': 'grams',
                        'g': 'grams',
                        'milliliters': 'ml',
                        'milliliter': 'ml',
                        'millilitres': 'ml',
                        'millilitre': 'ml',
                        'dbfg': 'bags',  # Map DBFG to bags as a reasonable default
                    }
                    
                    mapped_unit = unit_mapping.get(request_unit, 'other')
                    self.fields['quantity_unit'].initial = mapped_unit
                    
                    # If we mapped to 'other', add a help text
                    if mapped_unit == 'other':
                        self.fields['quantity_unit'].help_text = f'Request specified: "{self.request_context.quantity_unit}". Please select the closest match or "Other".'
        
        # Make fields conditional based on donation type
        self.fields['item_name'].required = False
        self.fields['quantity'].required = False
        self.fields['quantity_unit'].required = False
        self.fields['amount'].required = False
        self.fields['subsidized_price'].required = False
        self.fields['subsidized_market_price'].required = False
        self.fields['subsidized_product_type'].required = False
        self.fields['subsidized_quantity'].required = False
        self.fields['subsidized_quantity_unit'].required = False
        self.fields['other_description'].required = False
        self.fields['csr_custom_subcategory'].required = False
        self.fields['mpesa_phone'].required = False
        self.fields['donation_category'].required = False
        self.fields['donation_mode'].required = False
        self.fields['delivery_method'].required = False
        
        # Add help text
        self.fields['donation_type'].help_text = 'Choose the type of donation you want to make'
        self.fields['delivery_method'].help_text = 'How would you like to deliver your donation?'
        self.fields['pickup_time'].help_text = 'When would you like to schedule pickup? (if applicable)'

    def clean(self):
        cleaned_data = super().clean()
        donation_type = cleaned_data.get('donation_type')
        donation_category = cleaned_data.get('donation_category')
        donation_mode = cleaned_data.get('donation_mode')
        foodbank = cleaned_data.get('foodbank')
        request_id = cleaned_data.get('request_id')
        
        # If donating to a specific request, get foodbank from request
        if request_id and not foodbank:
            try:
                foodbank_request = FoodBankRequest.objects.get(pk=request_id, status='active')
                cleaned_data['foodbank'] = foodbank_request.foodbank
            except FoodBankRequest.DoesNotExist:
                raise forms.ValidationError('The selected request is no longer active.')
        
        # Validate based on donation category and mode
        if donation_category in ['food', 'non_food']:
            if donation_mode == 'free':
                # Free donation validation (item type)
                if not cleaned_data.get('item_name'):
                    raise forms.ValidationError('Item name is required for free donations.')
                if not cleaned_data.get('quantity'):
                    raise forms.ValidationError('Quantity is required for free donations.')
                if not cleaned_data.get('quantity_unit'):
                    raise forms.ValidationError('Quantity unit is required for free donations.')
                
                # Set donation_type to 'item' for free donations
                cleaned_data['donation_type'] = 'item'
                
            elif donation_mode == 'subsidized':
                # Subsidized donation validation
                market_price = cleaned_data.get('subsidized_market_price')
                subsidized_price = cleaned_data.get('subsidized_price')
                
                if not cleaned_data.get('subsidized_product_type'):
                    raise forms.ValidationError('Product type is required for subsidized donations.')
                if not market_price or market_price <= 0:
                    raise forms.ValidationError('A valid market price is required for subsidized goods donations.')
                if not subsidized_price or subsidized_price <= 0:
                    raise forms.ValidationError('A valid subsidized price is required for subsidized goods donations.')
                if subsidized_price >= market_price:
                    raise forms.ValidationError('Subsidized price must be less than market price.')
                if not cleaned_data.get('subsidized_quantity'):
                    raise forms.ValidationError('Quantity is required for subsidized donations.')
                if not cleaned_data.get('subsidized_quantity_unit'):
                    raise forms.ValidationError('Quantity unit is required for subsidized donations.')
                
                # Calculate discount percentage automatically
                discount_amount = market_price - subsidized_price
                discount_percentage = (discount_amount / market_price) * 100
                cleaned_data['subsidized_discount_percentage'] = discount_percentage
                
                # Set donation_type to 'subsidized'
                cleaned_data['donation_type'] = 'subsidized'
        
        elif donation_category == 'monetary':
            # Monetary donation validation
            if not cleaned_data.get('amount') or cleaned_data.get('amount') <= 0:
                raise forms.ValidationError('A valid amount is required for monetary donations.')
            
            # Set donation_type to 'money'
            cleaned_data['donation_type'] = 'money'
            # When donating to a request, use the request's category (food/non_food) so it matches the foodbank requests table
            if request_id:
                try:
                    foodbank_request = FoodBankRequest.objects.get(pk=request_id, status='active')
                    req_type = getattr(getattr(foodbank_request, 'original_request', None), 'request_type', None) or getattr(foodbank_request, 'donation_type', None)
                    if req_type in ('food', 'non_food'):
                        cleaned_data['donation_category'] = 'monetary'
                except FoodBankRequest.DoesNotExist:
                    pass
        
        elif donation_category == 'other':
            # Other donation validation
            if not cleaned_data.get('other_description'):
                raise forms.ValidationError('Description is required for special donations.')

            # Set donation_type to 'other'
            cleaned_data['donation_type'] = 'other'

        elif donation_mode == 'discussion':
            # Discussion mode validation (for other donations)
            if not cleaned_data.get('other_description'):
                raise forms.ValidationError('Description is required for donations requiring discussion.')

            # Set donation_type to 'other' and ensure discussion is required
            cleaned_data['donation_type'] = 'other'
            
        
        elif donation_category == 'csr':
            csr_subcategory = cleaned_data.get('csr_subcategory')
            csr_custom_subcategory = cleaned_data.get('csr_custom_subcategory')

            if not csr_subcategory:
                self.add_error('csr_subcategory', 'CSR subcategory is required.')
            if not cleaned_data.get('csr_description'):
                self.add_error('csr_description', 'CSR description is required.')

            if csr_subcategory == 'other':
                if not csr_custom_subcategory:
                    self.add_error('csr_custom_subcategory', 'Please specify the CSR type.')
            else:
                # Clear custom label when a predefined subcategory is chosen
                cleaned_data['csr_custom_subcategory'] = ''

            cleaned_data['donation_type'] = 'csr'
            cleaned_data['donation_mode'] = 'csr'  # ensure consistency

        else:
            self.add_error('donation_category', 'Please select a valid donation category.')

        # Delivery method handling
        if donation_category == 'monetary':
            # Monetary donations don't need delivery logistics
            cleaned_data['delivery_method'] = ''
        elif donation_category == 'csr':
            # Allow donors to specify how CSR contributions will be handed over (optional)
            pass
        else:
            if not cleaned_data.get('delivery_method'):
                self.add_error('delivery_method', 'Please select a delivery method.')



        
        # Ensure foodbank is selected (this should be handled by the view for general donations)
        # We'll skip this validation for general donations since foodbank is set in the view
        
        return cleaned_data

    def save(self, commit=True):
        donation = super().save(commit=False)
        
        # Set foodbank from request context if available
        if self.request_context and hasattr(self.request_context, 'foodbank'):
            donation.foodbank = self.request_context.foodbank
        
        if commit:
            donation.save()
        return donation

class FoodBankRequestForm(forms.ModelForm):
    custom_unit = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter custom unit (e.g., boxes, containers, etc.)',
            'style': 'display: none;'  # Initially hidden
        }),
        help_text="Specify your custom unit of measurement"
    )
    
    deadline = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control',
        }),
        help_text="Required: Set a deadline for when donations are needed. Requests without deadlines will not be shown to donors after the deadline passes."
    )
    
    class Meta:
        model = FoodBankRequest
        fields = [
            'donation_type',
            'title',
            'description',
            'priority',
            'delivery_method',
            'quantity_needed',
            'quantity_unit',
            'custom_unit',
            'deadline',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '30',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'maxlength': '400',
            }),
            'donation_type': forms.Select(attrs={'class': 'form-control'}),  # dropdown for donation_type
            'delivery_method': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use only the system default unit list for request creation/editing.
        # Custom units remain request-specific via quantity_unit='other' + custom_unit text.
        unit_choices = list(QUANTITY_UNITS)
        current_unit = getattr(self.instance, 'quantity_unit', None)
        if current_unit and not any(code == current_unit for code, _ in unit_choices):
            fallback_label = getattr(self.instance, 'custom_unit', None) or str(current_unit).replace('_', ' ').title()
            unit_choices.append((current_unit, fallback_label))
        if not any(code == 'other' for code, _ in unit_choices):
            unit_choices.append(('other', 'Other'))
        self.fields['quantity_unit'].choices = unit_choices
        self.instance._meta.get_field('quantity_unit').choices = unit_choices
        self.fields['quantity_needed'].required = True
        self.fields['quantity_unit'].required = True
        self.fields['delivery_method'].required = True
        self.fields['delivery_method'].choices = [
            ('', 'Select delivery method'),
            *list(FoodBankRequest.DELIVERY_METHOD_CHOICES),
        ]

    def clean(self):
        cleaned_data = super().clean()
        quantity_needed = cleaned_data.get('quantity_needed')
        quantity_unit = cleaned_data.get('quantity_unit')
        delivery_method = cleaned_data.get('delivery_method')

        if not quantity_needed:
            self.add_error('quantity_needed', 'Please provide the quantity needed for this request.')

        if not quantity_unit:
            self.add_error('quantity_unit', 'Please select a unit of measurement for the quantity provided.')

        if not delivery_method and 'delivery_method' not in self.errors:
            self.add_error('delivery_method', 'Please select a delivery method for this request.')

        return cleaned_data

    def clean_title(self):
        title = (self.cleaned_data.get('title') or '').strip()
        if len(title) > 30:
            raise forms.ValidationError('Title must be 30 characters or fewer.')
        return title

    def clean_description(self):
        description = (self.cleaned_data.get('description') or '').strip()
        if len(description) > 400:
            raise forms.ValidationError('Description must be 400 characters or fewer.')
        return description

class FoodBankProfileForm(forms.ModelForm):
    class Meta:
        model = FoodBankProfile
        fields = [
            'foodbank_name',
            'contact_person',
            'address',
            'service_type',
            'authority_picture',
            'urgent_request_picture'
        ]
        widgets = {
            'foodbank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter foodbank name'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter contact person name'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter address'
            }),
            'service_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'authority_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'urgent_request_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make image fields optional for updates
        self.fields['authority_picture'].required = False
        self.fields['urgent_request_picture'].required = False

class FoodBankPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        }),
        label='Current Password'
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your new password'
        }),
        label='New Password'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your new password'
        }),
        label='Confirm New Password'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Your current password is incorrect.')
        return old_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('The two password fields didn\'t match.')
        return password2

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if password1:
            # Add your password validation here
            if len(password1) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
            if not any(c.isupper() for c in password1):
                raise forms.ValidationError('Password must contain at least one uppercase letter.')
            if not any(c.islower() for c in password1):
                raise forms.ValidationError('Password must contain at least one lowercase letter.')
            if not any(c.isdigit() for c in password1):
                raise forms.ValidationError('Password must contain at least one number.')
        return password1

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user

class DonorProfileForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        required=True
    )
    phone_number = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        }),
        required=True
    )
    
    class Meta:
        model = DonorProfile
        fields = [
            'full_name',
            'location',
            'is_organization',
            'organization_name'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your location (City, Country)'
            }),
            'is_organization': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'organization_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter organization name'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email
            self.fields['phone_number'].initial = self.user.phone_number

    def clean_organization_name(self):
        is_organization = self.cleaned_data.get('is_organization')
        organization_name = self.cleaned_data.get('organization_name')
        
        if is_organization and not organization_name:
            raise forms.ValidationError('Organization name is required when registering as an organization.')
        
        return organization_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Update user fields
        if self.user:
            self.user.email = self.cleaned_data['email']
            self.user.phone_number = self.cleaned_data['phone_number']
            if commit:
                self.user.save()
        
        if commit:
            profile.save()
        
        return profile

class DonorPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        }),
        label='Current Password'
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your new password'
        }),
        label='New Password'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your new password'
        }),
        label='Confirm New Password'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Your current password is incorrect.')
        return old_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('The two password fields didn\'t match.')
        return password2

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if password1:
            if len(password1) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
            if not any(c.isupper() for c in password1):
                raise forms.ValidationError('Password must contain at least one uppercase letter.')
            if not any(c.islower() for c in password1):
                raise forms.ValidationError('Password must contain at least one lowercase letter.')
            if not any(c.isdigit() for c in password1):
                raise forms.ValidationError('Password must contain at least one number.')
        return password1

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user

class DonationAllocationForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=RecipientProfile.objects.all(),
        empty_label="Select a Recipient",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = DonationAllocation
        fields = ['recipient', 'quantity', 'amount']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        self.donation = kwargs.pop('donation', None)
        super().__init__(*args, **kwargs)
        
        if self.donation:
            # Set field labels based on donation type
            if self.donation.donation_type == 'item':
                self.fields['quantity'].label = f'Quantity ({self.donation.quantity_unit or "items"})'
                self.fields['amount'].widget = forms.HiddenInput()
            elif self.donation.donation_type in ['money', 'subsidized']:
                self.fields['quantity'].widget = forms.HiddenInput()
                self.fields['amount'].label = 'Amount'
            
            # Set max values based on available donation
            if self.donation.donation_type == 'item':
                self.fields['quantity'].widget.attrs['max'] = self.donation.quantity
            elif self.donation.donation_type == 'money':
                self.fields['amount'].widget.attrs['max'] = self.donation.amount
            elif self.donation.donation_type == 'subsidized':
                self.fields['amount'].widget.attrs['max'] = self.donation.subsidized_price

    def clean(self):
        cleaned_data = super().clean()
        recipient = cleaned_data.get('recipient')
        quantity = cleaned_data.get('quantity')
        amount = cleaned_data.get('amount')

        if not recipient:
            raise forms.ValidationError('Please select a recipient.')

        if self.donation:
            # Check if allocation exceeds available donation
            if self.donation.donation_type == 'item':
                if not quantity:
                    raise forms.ValidationError('Quantity is required for item donations.')
                if quantity > self.donation.quantity:
                    raise forms.ValidationError(f'Quantity cannot exceed available donation ({self.donation.quantity}).')
            elif self.donation.donation_type in ['money', 'subsidized']:
                if not amount:
                    raise forms.ValidationError('Amount is required for money/subsidized donations.')
                max_amount = self.donation.amount if self.donation.donation_type == 'money' else self.donation.subsidized_price
                if amount > max_amount:
                    raise forms.ValidationError(f'Amount cannot exceed available donation (${max_amount}).')

        return cleaned_data




class RecipientRequestForm(forms.ModelForm):
    class Meta:
        model = RecipientRequest
        fields = [
            "foodbank",
            "title",
            "description",
            "quantity",
            "quantity_unit",
            "delivery_method",
            "location",
            "is_anonymous",
        ]
        widgets = {
            "foodbank": forms.Select(attrs={
                "class": "form-control"
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter request title (e.g., Food Aid, Clothes, etc.)"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Describe your need..."
            }),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter quantity",
                "min": "1"
            }),
            "quantity_unit": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. kg, packets, liters"
            }),
            "delivery_method": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Pick-up, Delivery"
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your location"
            }),
            "is_anonymous": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_anonymous = cleaned_data.get("is_anonymous")
        if is_anonymous:
            cleaned_data["foodbank"] = None  # ignore selected foodbank
        return cleaned_data
   

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than 0.")
        return quantity


class RecipientProfileForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        required=True
    )
    phone_number = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        }),
        required=True
    )
    
    class Meta:
        model = RecipientProfile
        fields = [
            'full_name',
            'location',
            'is_organization',
            'organization_name',
            'consent_subsidized_goods'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your location'
            }),
            'is_organization': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'organization_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter organization name'
            }),
            'consent_subsidized_goods': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email
            self.fields['phone_number'].initial = self.user.phone_number

    def clean_organization_name(self):
        is_organization = self.cleaned_data.get('is_organization')
        organization_name = self.cleaned_data.get('organization_name')
        
        if is_organization and not organization_name:
            raise forms.ValidationError('Organization name is required when registering as an organization.')
        
        return organization_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Update user fields
        if self.user:
            self.user.email = self.cleaned_data['email']
            self.user.phone_number = self.cleaned_data['phone_number']
            if commit:
                self.user.save()
        
        if commit:
            profile.save()
        
        return profile

class RecipientPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        }),
        label='Current Password'
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your new password'
        }),
        label='New Password'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your new password'
        }),
        label='Confirm New Password'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Your current password is incorrect.')
        return old_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('The two password fields didn\'t match.')
        return password2

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if password1:
            if len(password1) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
            if not any(c.isupper() for c in password1):
                raise forms.ValidationError('Password must contain at least one uppercase letter.')
            if not any(c.islower() for c in password1):
                raise forms.ValidationError('Password must contain at least one lowercase letter.')
            if not any(c.isdigit() for c in password1):
                raise forms.ValidationError('Password must contain at least one number.')
        return password1

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user

class AdminRegistrationForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        strip=False,
        error_messages={
            'required': 'Phone number is required.'
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'password1',
            'data-toggle': 'password'
        }),
        help_text='Password must be at least 8 characters long.'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'id': 'password2'
        })
    )
    admin_code = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter admin authorization code'
        }),
        help_text='Enter the admin authorization code to proceed'
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'password1', 'password2', 'admin_code')

    def clean_phone_number(self):
        phone_number = (self.cleaned_data.get('phone_number') or '').strip()
        if not phone_number:
            raise forms.ValidationError('Phone number is required.')
        return phone_number

    def clean_admin_code(self):
        admin_code = self.cleaned_data.get('admin_code')
        
        # Import here to avoid circular imports
        from .models import AdminCode
        
        try:
            code_obj = AdminCode.objects.get(code=admin_code, is_active=True, used_count=0)
            # Store the code object for later use in save method
            self._admin_code_obj = code_obj
            return admin_code
        except AdminCode.DoesNotExist:
            raise forms.ValidationError('Invalid or already-used admin authorization code. Access denied.')
        
        return admin_code

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'ADMIN'
        user.is_staff = True  # Give admin users staff privileges
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        
        if commit:
            from django.db import transaction
            from .models import AdminCode

            with transaction.atomic():
                user.save()
                if hasattr(self, '_admin_code_obj'):
                    code_obj = AdminCode.objects.select_for_update().get(pk=self._admin_code_obj.pk)
                    if not code_obj.is_active or code_obj.used_count > 0:
                        raise forms.ValidationError('This admin code has already been used.')
                    code_obj.mark_as_used(user)
        
        return user

class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ["message", "impact_image", "display_on_public"]
        widgets = {
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Share your story and the impact of the help you received. Be specific about how the assistance helped you..."
            }),
            "impact_image": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*"
            }),
            "display_on_public": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }
        labels = {
            "message": "Your Testimonial",
            "impact_image": "Impact Photo (Optional)",
            "display_on_public": "I agree to display this testimonial publicly after approval"
        }
        help_texts = {
            "message": "Share your experience and how the assistance made a difference in your life",
            "impact_image": "Upload a photo showing the impact (e.g., food received, items distributed, etc.)",
            "display_on_public": "Your testimonial will be reviewed by admin before being displayed publicly"
        }

class FoodbankTestimonialForm(forms.ModelForm):
    class Meta:
        model = FoodbankTestimonial
        fields = ["message", "impact_image", "display_on_public"]
        widgets = {
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Share your experience with donors and the platform. Describe how donations have helped your food bank serve the community..."
            }),
            "impact_image": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*"
            }),
            "display_on_public": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }
        labels = {
            "message": "Your Testimonial",
            "impact_image": "Impact Photo (Optional)",
            "display_on_public": "I agree to display this testimonial publicly after approval"
        }
        help_texts = {
            "message": "Share your experience working with donors and how their contributions have made a difference",
            "impact_image": "Upload a photo showing the impact of donations (e.g., food distribution, community events, etc.). Recommended: 1600x900 px (16:9), minimum 1200x675 px. Image may be center-cropped on cards, so keep key content in the middle.",
            "display_on_public": "Your testimonial will be reviewed by admin before being displayed publicly"
        }


class DonorTestimonialForm(forms.ModelForm):
    class Meta:
        model = DonorTestimonial
        fields = ["message", "public_website_url", "impact_image", "display_on_public"]
        widgets = {
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Share your experience as a donor and the impact you've witnessed. Describe how giving has affected you and the difference you've seen in the community..."
            }),
            "public_website_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://example.com"
            }),
            "impact_image": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*"
            }),
            "display_on_public": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }
        labels = {
            "message": "Your Testimonial",
            "public_website_url": "Public Website URL (Optional)",
            "impact_image": "Impact Photo (Optional)",
            "display_on_public": "I agree to display this testimonial publicly after approval"
        }
        help_texts = {
            "message": "Share your experience as a donor, the joy of giving, and any impact you've witnessed firsthand",
            "public_website_url": "If you have a public website, you can share it here.",
            "impact_image": "Upload a photo related to your donation experience (e.g., donation events, community impact, etc.)",
            "display_on_public": "Your testimonial will be reviewed by admin before being displayed publicly"
        }


class SubscriptionPaymentForm(forms.ModelForm):
    """Form for food banks to submit subscription payment evidence"""
    class Meta:
        model = SubscriptionPayment
        fields = [
            'plan_type',
            'payment_method',
            'amount',
            'transaction_reference',
            'payment_date',
            'payment_evidence',
            'notes'
        ]
        widgets = {
            'plan_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount paid',
                'step': '0.01',
                'required': True
            }),
            'transaction_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., M-Pesa code: QH12ABC34D or Bank ref: TXN123456',
                'required': True
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'payment_evidence': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional information about your payment (optional)'
            }),
        }
        labels = {
            'plan_type': 'Subscription Plan',
            'payment_method': 'Payment Method',
            'amount': 'Amount Paid (KSH)',
            'transaction_reference': 'Transaction Reference/Code',
            'payment_date': 'Payment Date',
            'payment_evidence': 'Payment Screenshot/Receipt',
            'notes': 'Additional Notes (Optional)'
        }
        help_texts = {
            'plan_type': 'Select the plan you are subscribing to',
            'payment_method': 'How did you make the payment?',
            'amount': 'Enter the exact amount you paid',
            'transaction_reference': 'Enter the M-Pesa code or bank transaction reference',
            'payment_date': 'When did you make the payment?',
            'payment_evidence': 'Upload a clear screenshot or photo of your payment confirmation',
            'notes': 'Any additional information we should know about your payment'
        }
    
    def clean_amount(self):
        """Validate that amount matches the selected plan"""
        amount = self.cleaned_data.get('amount')
        plan_type = self.cleaned_data.get('plan_type')
        
        if plan_type == 'monthly' and amount != 2000:
            raise ValidationError('Monthly plan costs KSH 2,000. Please enter the correct amount.')
        elif plan_type == 'yearly' and amount != 10000:
            raise ValidationError('Yearly plan costs KSH 10,000. Please enter the correct amount.')
        
        return amount
    
    def clean_payment_evidence(self):
        """Validate payment evidence file"""
        evidence = self.cleaned_data.get('payment_evidence')
        
        if evidence:
            # Check file size (max 5MB)
            if evidence.size > 5 * 1024 * 1024:
                raise ValidationError('File size must be less than 5MB.')
            
            # Check file type
            if not evidence.content_type.startswith('image/'):
                raise ValidationError('Please upload an image file (JPG, PNG, etc.).')
        
        return evidence


class SystemSupportDonationForm(forms.ModelForm):
    """Form for donors to submit system support donations"""
    
    class Meta:
        model = SystemSupportDonation
        fields = ['amount', 'payment_proof', 'transaction_reference', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount in KES',
                'min': '50',
                'max': '100000000',
                'step': '0.01',
                'required': True
            }),
            'payment_proof': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': True
            }),
            'transaction_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'M-Pesa code or bank reference (optional)',
                'maxlength': '100'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional notes about your donation (optional)'
            }),
        }
        labels = {
            'amount': 'Donation Amount (KES)',
            'payment_proof': 'Payment Proof',
            'transaction_reference': 'Transaction Reference',
            'notes': 'Additional Notes',
        }
        help_texts = {
            'amount': 'Enter the amount you donated to support FoodBank Hub',
            'payment_proof': 'Upload a screenshot or photo of your payment confirmation',
            'transaction_reference': 'M-Pesa confirmation code, bank reference number, etc.',
            'notes': 'Any additional information you\'d like to share',
        }
    
    def clean_amount(self):
        """Validate donation amount"""
        amount = self.cleaned_data.get('amount')
        if amount and amount < 50:
            raise forms.ValidationError('Minimum donation amount is KES 50.')
        if amount and amount > 100000000:
            raise forms.ValidationError('Maximum donation amount is KES 100,000,000.')
        return amount
    
    def clean_payment_proof(self):
        """Validate payment proof image"""
        proof = self.cleaned_data.get('payment_proof')
        
        if proof:
            # Check file size (max 5MB)
            if proof.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 5MB.')
            
            # Check file type
            if not proof.content_type.startswith('image/'):
                raise forms.ValidationError('Please upload an image file (JPG, PNG, etc.).')
        
        return proof

