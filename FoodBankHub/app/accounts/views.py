"""
Accounts module views (trimmed).

This module keeps only auth/account-related endpoints referenced by `app/accounts/urls.py`.
Implementation is delegated to the existing monolith (`authentication.views`) so the project
continues to work today while the future microservice modules stay clean and domain-scoped.
"""

from authentication.views import (
    login_view,
    logout_view,
    DonorRegistrationView,
    FoodBankRegistrationView,
    RecipientRegistrationView,
    AdminRegistrationView,
)
from django.utils.timezone import now

from .models import (

    CustomUser, DonorProfile, FoodBankProfile, RecipientProfile, 

    Donation, FoodBankRequest, DonationAllocation, RecipientRequest, 

    Notification, Testimonial, PaymentTransaction, FoodBankGalleryPhoto,

    DonationDiscussion, DonationDiscussionMessage, QUANTITY_UNITS, QuantityUnit,

    RequestManagement, Subscription, AccountDeletionRequest, SystemSupportDonation, DonationResponse,

    UnspecifiedDonationManagement

)

from .donation_views import (
    get_display_status,
    STATUS_CLASS_MAP,
    _get_foodbank_export_type_display,
    _get_foodbank_export_category_display,
)

from .forms import (

    CustomLoginForm, DonorRegistrationForm,

    FoodBankRegistrationForm, RecipientRegistrationForm, AdminRegistrationForm,

    DonationForm, FoodBankRequestForm, FoodBankProfileForm, FoodBankPasswordChangeForm,

    DonationAllocationForm, DonorProfileForm, DonorPasswordChangeForm,

    RecipientRequestForm, TestimonialForm, RecipientProfileForm, RecipientPasswordChangeForm,

    SystemSupportDonationForm

)

from .available_donations_exports import (
    export_available_donations_pdf as available_donations_pdf_report,
    export_available_donations_csv as available_donations_csv_report,
    export_available_donations_excel as available_donations_excel_report,
    resolve_available_donation_description,
)

SUPPORT_MESSAGE_MIN_LENGTH = 15

from django.views.decorators.csrf import csrf_exempt

from django.views.decorators.csrf import csrf_exempt

from django.http import HttpResponse

import json

from django.http import HttpResponse

from datetime import datetime

from django.http import JsonResponse

from django.db.models import Q

from django.core.paginator import Paginator

from django.utils.dateparse import parse_date

stripe.api_key = settings.STRIPE_SECRET_KEY

from django.db.models import Q

from django.core.paginator import Paginator

from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.db import transaction

from django.shortcuts import get_object_or_404, redirect

from django.core.exceptions import FieldDoesNotExist

from django.db.models import Q

from django.core.mail import send_mail

from django.utils import timezone

from django.db.models import Sum

from django.contrib import messages

from django.shortcuts import get_object_or_404, redirect

from django.shortcuts import redirect, get_object_or_404

from django.contrib import messages

from .models import RequestManagement

from django.utils import timezone

from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required

from django.db.models import Q

from django.shortcuts import get_object_or_404, redirect

from django.contrib import messages

from .models import RequestManagement, Donation

import openpyxl

from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from openpyxl.utils import get_column_letter

from django.contrib import messages

from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required

def login_view(request):

    if request.user.is_authenticated:

        # Redirect admin users to custom admin dashboard

        if request.user.is_staff:

            return redirect('custom_admin:dashboard')

        return redirect('dashboard')

    

    if request.method == 'POST':

        form = CustomLoginForm(data=request.POST)

        if form.is_valid():

            user = form.get_user()

            

            # Check if user is a foodbank and if they're approved

            if user.user_type == 'FOODBANK':

                try:

                    foodbank_profile = user.foodbank_profile

                    if foodbank_profile.is_approved == 'pending':

                        messages.error(

                            request, 

                            'Your food bank application is still under review. '

                            'You will receive an email notification once approved.'

                        )

                        return render(request, 'authentication/login.html', {'form': form})

                    elif foodbank_profile.is_approved == 'rejected':

                        messages.error(

                            request, 

                            'Your food bank application has been rejected. '

                            'Please contact support for more information.'

                        )

                        return render(request, 'authentication/login.html', {'form': form})

                except FoodBankProfile.DoesNotExist:

                    messages.error(request, 'Food bank profile not found. Please contact support.')

                    return render(request, 'authentication/login.html', {'form': form})

            

            login(request, user)

            

            # Redirect admin users to custom admin dashboard

            if user.is_staff:

                messages.success(request, f'Welcome back, {user.email}!')

                return redirect('custom_admin:dashboard')

            

            # Use role-aware dashboard routing for all non-staff users.
            return redirect('dashboard')

    else:

        form = CustomLoginForm()

    return render(request, 'authentication/login.html', {'form': form})

def logout_view(request):

    logout(request)

    return redirect('home')

class DonorRegistrationView(CreateView):

    form_class = DonorRegistrationForm

    template_name = 'authentication/register_donor.html'

    success_url = reverse_lazy('login')



    def form_valid(self, form):

        response = super().form_valid(form)

        # Send welcome email to new donor

        try:

            send_welcome_email(self.object, self.object.user_type)

        except Exception as e:

            # Log error but don't break registration

            print(f"Failed to send welcome email: {e}")

        messages.success(self.request, 'Registration successful! You can now log in.')

        return response

class FoodBankRegistrationView(CreateView):

    form_class = FoodBankRegistrationForm

    template_name = 'authentication/register_foodbank.html'

    success_url = reverse_lazy('registration_pending')



    def form_valid(self, form):

        response = super().form_valid(form)

        # Send application received email to new foodbank

        try:

            send_application_received_email(self.object)

        except Exception as e:

            # Log error but don't break registration

            print(f"Failed to send application received email: {e}")

        

        # Notify admins about new application

        try:

            notify_admins_new_application(self.object.foodbank_profile)

        except Exception as e:

            print(f"Failed to notify admins: {e}")

            

        messages.success(

            self.request, 

            'Registration submitted successfully! Your application is now under review. '

            'You will receive an email notification once your application has been approved.'

        )

        return response

class RecipientRegistrationView(CreateView):

    form_class = RecipientRegistrationForm

    template_name = 'authentication/register_recipient.html'

    success_url = reverse_lazy('login')



    def form_valid(self, form):

        response = super().form_valid(form)

        # Send welcome email to new recipient

        try:

            send_welcome_email(self.object, self.object.user_type)

        except Exception as e:

            # Log error but don't break registration

            print(f"Failed to send welcome email: {e}")

        messages.success(self.request, 'Registration successful! You can now log in.')

        return response

class AdminRegistrationView(CreateView):

    form_class = AdminRegistrationForm

    template_name = 'authentication/register_admin.html'

    success_url = reverse_lazy('login')



    def form_valid(self, form):

        response = super().form_valid(form)

        # Send welcome email to new admin

        try:

            send_welcome_email(self.object, self.object.user_type)

        except Exception as e:

            # Log error but don't break registration

            print(f"Failed to send welcome email: {e}")

        messages.success(self.request, 'Admin registration successful! You can now log in with administrative privileges.')

        return response
