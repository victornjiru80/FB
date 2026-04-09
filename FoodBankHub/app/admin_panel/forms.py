from django import forms

from authentication.models import CustomUser, DonorProfile, FoodBankProfile, RecipientProfile


class CustomUserAdminUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'phone_number', 'is_active', 'is_staff']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DonorProfileAdminForm(forms.ModelForm):
    class Meta:
        model = DonorProfile
        fields = ['full_name', 'is_organization', 'organization_name', 'location']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_organization': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }


class FoodBankProfileAdminForm(forms.ModelForm):
    class Meta:
        model = FoodBankProfile
        fields = [
            'foodbank_name',
            'contact_person',
            'address',
            'service_type',
            'contact_email',
            'contact_phone',
            'website_url',
            'established_year',
        ]
        widgets = {
            'foodbank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'service_type': forms.Select(attrs={'class': 'form-select'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website_url': forms.URLInput(attrs={'class': 'form-control'}),
            'established_year': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class RecipientProfileAdminForm(forms.ModelForm):
    class Meta:
        model = RecipientProfile
        fields = ['full_name', 'location', 'is_organization', 'organization_name']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'is_organization': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
