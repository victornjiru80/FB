"""
Donations module views (trimmed).

Keeps only donation/payment endpoints referenced by `app/donations/urls.py`.
"""

from authentication.views import (
    select_foodbank_for_donation,
    donate_to_foodbank_general,
    donate_to_foodbank,
    allocate_donation,
    view_donation_allocations,
    accept_donation,
    decline_donation,
    create_payment_intent,
    confirm_payment,
    stripe_webhook,
    payment_success,
    payment_cancelled,
    mpesa_callback,
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

def _get_quantity_units():
    default_units = list(QUANTITY_UNITS)
    db_units = list(QuantityUnit.objects.values_list('code', 'label'))

    # Start with the full default list, then append any custom units from DB.
    merged_units = []
    default_codes = {code for code, _ in default_units}
    db_by_code = {code: label for code, label in db_units}

    for code, label in default_units:
        merged_units.append((code, db_by_code.get(code, label)))

    for code, label in db_units:
        if code not in default_codes:
            merged_units.append((code, label))

    return merged_units

def _redirect_back_or_default(request, fallback='foodbank_requests_view'):
    """Redirect to a safe caller-provided next URL or a fallback view name."""
    next_url = (request.POST.get('next') or request.GET.get('next') or '').strip()
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect(fallback)

def select_foodbank_for_donation(request):

    """Step 1: Select a food bank for general donation"""

    if request.user.user_type != 'DONOR':

        messages.error(request, 'Only donors can make donations.')

        return redirect('dashboard')

    

    # Get all approved food banks with their public profile info

    foodbanks = FoodBankProfile.objects.select_related('user').filter(

        user__is_active=True,

        is_approved='approved'

    ).order_by('foodbank_name')

    

    context = {

        'foodbanks': foodbanks,

    }

    return render(request, 'donor/select_foodbank.html', context)

def donate_to_foodbank_general(request, foodbank_id):

    """Step 2: Make donation to selected food bank"""

    if request.user.user_type != 'DONOR':

        messages.error(request, 'Only donors can make donations.')

        return redirect('dashboard')

    

    try:

        foodbank = FoodBankProfile.objects.get(id=foodbank_id)

    except FoodBankProfile.DoesNotExist:

        messages.error(request, 'Food bank not found.')

        return redirect('donate')

    

    if request.method == 'POST':

        submission_token = (request.POST.get('submission_token') or '').strip()

        expected_token = request.session.get('donate_general_submission_token')

        if not expected_token or not submission_token or submission_token != expected_token:

            messages.error(request, 'Please refresh the page and try submitting again.')

            return redirect(request.path)

        

        post_data = request.POST.copy()
        custom_quantity_unit = (post_data.get('custom_quantity_unit') or '').strip()
        custom_subsidized_unit = (post_data.get('custom_subsidized_quantity_unit') or '').strip()
        if (post_data.get('quantity_unit') or '').strip().lower() == 'other' and custom_quantity_unit:
            post_data['quantity_unit'] = custom_quantity_unit
        if (post_data.get('subsidized_quantity_unit') or '').strip().lower() == 'other' and custom_subsidized_unit:
            post_data['subsidized_quantity_unit'] = custom_subsidized_unit

        form = DonationForm(post_data)

        # Remove foodbank from form validation since it's pre-selected

        if 'foodbank' in form.fields:

            del form.fields['foodbank']

        if form.is_valid():

            cache_key = f"donate_general_submit:{request.user.id}:{submission_token}"

            if not cache.add(cache_key, True, timeout=120):

                messages.info(request, 'This donation has already been submitted.')

                return redirect('donor_unspecified_donations_detail')



            try:

                donation = form.save(commit=False)

                donation.donor = request.user

                donation.foodbank = foodbank  # Set the selected foodbank

                

                # Handle 'other' and 'csr' type donations - enable discussion

                if donation.donation_type in ['other', 'csr']:

                    donation.requires_discussion = True

                    donation.discussion_status = 'pending'

                

                # Create notification for food bank

                Notification.objects.create(

                    user=donation.foodbank.user,

                    notification_type='donation_received',

                    message=f'New donation received from {request.user.email}: {donation.get_donation_display()}'

                )

                

                donation.save()



                request.session.pop('donate_general_submission_token', None)

                

                # Create UnspecifiedDonationManagement for general donations (not subsidized)

                # This enables the foodbank -> recipient approval workflow

                if donation.foodbank_request is None and donation.donation_mode != 'subsidized':

                    from .models import UnspecifiedDonationManagement

                    UnspecifiedDonationManagement.objects.create(donation=donation)

                

                # For 'other' and 'csr' type donations, notify foodbank about new discussion opportunity

                if donation.donation_type in ['other', 'csr']:

                    # Notify foodbank about the new donation requiring discussion

                    Notification.objects.create(

                        user=donation.foodbank.user,

                        notification_type='new_donor',

                        message=f'New {donation.get_donation_type_display()} donation requires discussion from {request.user.email}'

                    )

                # Send confirmation email in background so response returns quickly
                try:
                    send_donation_confirmation_email_async(donation)
                except Exception as e:
                    logger.exception("Failed to queue donation confirmation email")
                

                messages.success(request, f'Your donation was submitted successfully! ðŸŽ‰ Thank you for helping {donation.foodbank.foodbank_name}.')

                if donation.foodbank_request is None:

                    if donation.donation_mode == 'subsidized' or donation.donation_type == 'subsidized':

                        return redirect('donor_subsidized_donations_detail')

                    return redirect('donor_unspecified_donations_detail')

                return redirect('donor_donations_list')

            except ValueError as e:

                messages.error(request, str(e))

        else:

            messages.error(request, 'Please correct the errors below.')

    else:

        # Create form without foodbank field since it's pre-selected

        form = DonationForm()

        if 'foodbank' in form.fields:

            del form.fields['foodbank']



    submission_token = uuid.uuid4().hex

    request.session['donate_general_submission_token'] = submission_token

    delivery_methods = [
        (value, 'Delivery' if value == 'dropoff' else label)
        for value, label in Donation.DELIVERY_METHODS
    ]

    

    context = {

        'form': form,

        'foodbank': foodbank,

        'submission_token': submission_token,

        'donation_types': Donation.DONATION_TYPES,

        'quantity_units': _get_quantity_units(),

        'delivery_methods': delivery_methods,

        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,

    }

    return render(request, 'donor/donate_to_foodbank_enhanced.html', context)

def donate_to_foodbank(request, request_id):

    """Handle donations to specific food bank requests"""

    if request.user.user_type != 'DONOR':

        messages.error(request, 'Only donors can make donations.')

        return redirect('dashboard')



    try:

        foodbank_request = FoodBankRequest.objects.get(pk=request_id, status='active')

    except FoodBankRequest.DoesNotExist:

        messages.error(request, 'Request not found or no longer active.')

        return redirect('dashboard')



    if request.method == 'POST':
        post_data = request.POST.copy()

        # Guard against overlong request titles flowing into CharField(max_length=255)
        # via hidden/default form values in request-response flow.
        for field_name in ('item_name', 'subsidized_product_type'):
            field_value = (post_data.get(field_name) or '').strip()
            if field_value:
                post_data[field_name] = field_value[:255]

        response_type = (post_data.get('response_type') or '').strip().lower()
        title_fallback = (foodbank_request.title or 'Request Item').strip()[:255]

        if response_type == 'free' and not (post_data.get('item_name') or '').strip():
            post_data['item_name'] = title_fallback

        if response_type == 'subsidized' and not (post_data.get('subsidized_product_type') or '').strip():
            post_data['subsidized_product_type'] = title_fallback

        form = DonationForm(post_data, request_context=foodbank_request)

        if form.is_valid():

            donation = form.save(commit=False)

            donation.donor = request.user

            donation.foodbank = foodbank_request.foodbank

            donation.foodbank_request = foodbank_request

            donation.status = 'pending'  # Set initial status to pending

            donation.save()

            

            # Update original request metadata so foodbank can review/accept

            original_req = foodbank_request.original_request

            if original_req:

                fields_to_update = []



                # Mark as awaiting foodbank action so Accept button shows up

                if getattr(original_req, 'status', None) not in ['awaiting_recipient', 'fulfilled']:

                    if original_req.status != 'donation_received':

                        original_req.status = 'donation_received'

                        fields_to_update.append('status')

                    if hasattr(original_req, 'awaiting_donors') and original_req.awaiting_donors:

                        original_req.awaiting_donors = False

                        fields_to_update.append('awaiting_donors')



                if fields_to_update:

                    original_req.save()



                # Don't append donor note to original_req

# Keep recipient notes in RequestManagement

# Donor note stays with the donation itself



            

            # Notifications (your existing logic)

            Notification.objects.create(

                user=request.user,

                notification_type='acknowledgement',

                message=f'Thank you for responding to the urgent request from {foodbank_request.foodbank.foodbank_name}.'

            )

            

            donation_display = donation.get_donation_display()

            Notification.objects.create(

                user=foodbank_request.foodbank.user,

                notification_type='donation_received',

                message=f'New donation pending review for request "{foodbank_request.title}": {donation_display} from {request.user.email}'

            )

            

            # Send email (your existing logic)

            try:
                send_donation_confirmation_email_async(donation)
            except Exception:
                logger.exception("Failed to queue donation confirmation email")
            

            messages.success(request, f'Donation submitted successfully! Your donation is pending review by {foodbank_request.foodbank.foodbank_name}. You will be notified once it is reviewed.')

            redirect_url = reverse('donor_donations_list')

            if foodbank_request.original_request is None:

                redirect_url = f"{redirect_url}?direct=1"

            return redirect(redirect_url)

        else:

            messages.error(request, 'Please correct the errors below.')

    else:

        form = DonationForm(request_context=foodbank_request)

    request_unit_value = (getattr(foodbank_request, 'quantity_unit', None) or '').strip()
    if request_unit_value == 'other' and getattr(foodbank_request, 'custom_unit', None):
        request_unit_value = (foodbank_request.custom_unit or '').strip()
    request_unit_label = request_unit_value or (_get_request_unit_label(foodbank_request) or '')

    request_card_description = (getattr(foodbank_request, 'description', '') or '').strip()
    linked_request = getattr(foodbank_request, 'linked_request_management', None) or getattr(foodbank_request, 'original_request', None)
    if linked_request and getattr(linked_request, 'description', None):
        request_card_description = (linked_request.description or '').strip()
    else:
        for marker in ('--- Recipient Note ---', '--- Acknowledgment Note', '--- Receipt Confirmed', '--- Donor Note'):
            if marker in request_card_description:
                request_card_description = request_card_description.split(marker)[0].strip()
    if not request_card_description:
        request_card_description = (foodbank_request.title or 'Request details').strip()

    request_title = (getattr(foodbank_request, 'title', '') or '').strip()
    normalized_title = ' '.join(request_title.split()).lower()
    normalized_description = ' '.join(request_card_description.split()).lower()
    show_request_card_description = bool(request_card_description and normalized_description != normalized_title)



    delivery_methods = [
        (value, 'Delivery' if value == 'dropoff' else label)
        for value, label in Donation.DELIVERY_METHODS
    ]

    context = {

        'form': form,

        'foodbank_request': foodbank_request,
        'request_card_description': request_card_description,
        'show_request_card_description': show_request_card_description,
        'request_unit_label': request_unit_label,
        'request_unit_value': request_unit_value,

        'donation_types': Donation.DONATION_TYPES,

        'quantity_units': _get_quantity_units(),

        'delivery_methods': delivery_methods,

    }

    return render(request, 'donor/donate.html', context)

def allocate_donation(request, donation_id):

    """Allocate a donation to one or more recipients"""

    if request.user.user_type != 'FOODBANK':

        messages.error(request, 'Only food banks can allocate donations.')

        return redirect('dashboard')

    

    try:

        donation = Donation.objects.get(id=donation_id, foodbank=request.user.foodbank_profile)

    except Donation.DoesNotExist:

        messages.error(request, 'Donation not found.')

        return redirect('dashboard')

    

    # Check if donation is already fully allocated

    if donation.is_fully_allocated():

        messages.warning(request, 'This donation has been fully allocated.')

        return redirect('dashboard')

    

    # Get remaining amount/quantity

    if donation.donation_type == 'item':

        remaining = donation.get_remaining_quantity()

    else:  # money or subsidized

        remaining = donation.get_remaining_amount()

    

    if request.method == 'POST':

        form = DonationAllocationForm(request.POST, donation=donation)

        if form.is_valid():

            allocation = form.save(commit=False)

            allocation.donation = donation

            allocation.save()

            

            # Create notification for recipient

            Notification.objects.create(

                user=allocation.recipient.user,

                notification_type='donation_received',

                message=f'You have been allocated {allocation.quantity or allocation.amount} from a donation by {donation.donor.email}.'

            )

            

            # Create notification for donor about allocation

            donation_display = f"{allocation.quantity} {donation.unit}" if allocation.quantity else f"KSH {allocation.amount}"

            Notification.objects.create(

                user=donation.donor,

                notification_type='donation_delivered',

                message=f'Your donation ({donation_display}) has been allocated to {allocation.recipient.full_name} by {donation.foodbank.foodbank_name}.'

            )

            

            messages.success(request, f'Donation allocated to {allocation.recipient.full_name} successfully!')

            return redirect('foodbank_donations')

    else:

        form = DonationAllocationForm(donation=donation)

    

    context = {

        'form': form,

        'donation': donation,

        'remaining': remaining,

        'allocations': donation.allocations.all(),

    }

    return render(request, 'authentication/allocate_donation.html', context)

def view_donation_allocations(request, donation_id):

    """View all allocations for a specific donation"""

    if request.user.user_type != 'FOODBANK':

        messages.error(request, 'Only food banks can view donation allocations.')

        return redirect('dashboard')

    

    try:

        donation = Donation.objects.get(id=donation_id, foodbank=request.user.foodbank_profile)

    except Donation.DoesNotExist:

        messages.error(request, 'Donation not found.')

        return redirect('dashboard')

    

    allocations = donation.allocations.all().order_by('-allocated_at')

    

    context = {

        'donation': donation,

        'allocations': allocations,

    }

    return render(request, 'authentication/view_donation_allocations.html', context)

def create_payment_intent(request):

    """Create a Stripe payment intent for credit card donations"""

    if request.user.user_type != 'DONOR':

        return JsonResponse({'error': 'Only donors can make payments'}, status=403)

    

    if request.method == 'POST':

        try:

            data = json.loads(request.body)

            amount = float(data.get('amount', 0))

            donation_id = data.get('donation_id')

            

            if amount <= 0:

                return JsonResponse({'error': 'Invalid amount'}, status=400)

            

            # Convert to cents for Stripe (KES to cents)

            amount_cents = int(amount * 100)

            

            # Create payment intent

            intent = stripe.PaymentIntent.create(

                amount=amount_cents,

                currency='kes',  # Kenyan Shillings

                metadata={

                    'donation_id': donation_id,

                    'donor_email': request.user.email,

                }

            )

            

            return JsonResponse({

                'client_secret': intent.client_secret,

                'payment_intent_id': intent.id

            })

            

        except stripe.error.StripeError as e:

            return JsonResponse({'error': str(e)}, status=400)

        except Exception as e:

            return JsonResponse({'error': 'An error occurred'}, status=500)

    

    return JsonResponse({'error': 'Method not allowed'}, status=405)

def confirm_payment(request):

    """Confirm payment and create donation record"""

    if request.user.user_type != 'DONOR':

        return JsonResponse({'error': 'Only donors can confirm payments'}, status=403)

    

    if request.method == 'POST':

        try:

            data = json.loads(request.body)

            payment_intent_id = data.get('payment_intent_id')

            foodbank_id = data.get('foodbank_id')

            donation_type = data.get('donation_type', 'money')

            message = data.get('message', '')

            

            # Retrieve payment intent from Stripe

            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            

            if intent.status != 'succeeded':

                return JsonResponse({'error': 'Payment not completed'}, status=400)

            

            # Get food bank

            try:

                foodbank = FoodBankProfile.objects.get(id=foodbank_id)

            except FoodBankProfile.DoesNotExist:

                return JsonResponse({'error': 'Food bank not found'}, status=404)

            

            # Create donation record

            amount = intent.amount / 100  # Convert from cents

            donation = Donation.objects.create(

                donor=request.user,

                donation_type=donation_type,

                foodbank=foodbank,

                amount=amount,

                message=message,

                delivery_status='pending'

            )

            

            # Create payment transaction record

            payment_transaction = PaymentTransaction.objects.create(

                donation=donation,

                stripe_payment_intent_id=payment_intent_id,

                payment_method='credit_card',

                status='completed',

                amount=amount,

                currency='KES',

                stripe_response=intent

            )

            payment_transaction.mark_completed()

            

            # Create notifications

            Notification.objects.create(

                user=request.user,

                notification_type='acknowledgement',

                message=f'Thank you for your credit card donation of KES {amount:,.2f} to {foodbank.foodbank_name}.'

            )

            

            Notification.objects.create(

                user=foodbank.user,

                notification_type='donation_received',

                message=f'Credit card donation received: KES {amount:,.2f} from {request.user.email}'

            )

            

            return JsonResponse({

                'success': True,

                'donation_id': donation.id,

                'message': 'Payment confirmed successfully!'

            })

            

        except stripe.error.StripeError as e:

            return JsonResponse({'error': f'Stripe error: {str(e)}'}, status=400)

        except Exception as e:

            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    

    return JsonResponse({'error': 'Method not allowed'}, status=405)

def stripe_webhook(request):

    """Handle Stripe webhooks for payment confirmations"""

    payload = request.body

    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    

    try:

        event = stripe.Webhook.construct_event(

            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET

        )

    except ValueError:

        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError:

        return HttpResponse(status=400)

    

    # Handle payment intent succeeded

    if event['type'] == 'payment_intent.succeeded':

        payment_intent = event['data']['object']

        

        # Find and update payment transaction

        try:

            payment_transaction = PaymentTransaction.objects.get(

                stripe_payment_intent_id=payment_intent['id']

            )

            payment_transaction.mark_completed()

        except PaymentTransaction.DoesNotExist:

            pass

    

    return HttpResponse(status=200)

def payment_success(request):

    """Payment success page"""

    donation_id = request.GET.get('donation_id')

    context = {

        'donation_id': donation_id,

    }

    return render(request, 'donor/payment_success.html', context)

def payment_cancelled(request):

    """Payment cancelled page"""

    return render(request, 'donor/payment_cancelled.html')

def mpesa_callback(request):

    """Handle M-Pesa payment callbacks"""

    if request.method == 'POST':

        try:

            import json

            callback_data = json.loads(request.body)

            

            # Extract callback data

            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})

            checkout_request_id = stk_callback.get('CheckoutRequestID')

            result_code = stk_callback.get('ResultCode')

            result_desc = stk_callback.get('ResultDesc')

            

            if checkout_request_id:

                try:

                    # Find the payment transaction

                    payment = PaymentTransaction.objects.get(

                        mpesa_checkout_request_id=checkout_request_id

                    )

                    

                    if result_code == 0:  # Success

                        # Extract M-Pesa receipt number from callback items

                        callback_metadata = stk_callback.get('CallbackMetadata', {})

                        items = callback_metadata.get('Item', [])

                        

                        mpesa_receipt = None

                        for item in items:

                            if item.get('Name') == 'MpesaReceiptNumber':

                                mpesa_receipt = item.get('Value')

                                break

                        

                        # Update payment transaction

                        payment.status = 'completed'

                        payment.mpesa_receipt_number = mpesa_receipt

                        payment.mark_completed()

                        

                        # Create success notification

                        Notification.objects.create(

                            user=payment.donation.donor,

                            notification_type='acknowledgement',

                            message=f'M-Pesa payment successful! Receipt: {mpesa_receipt}. Thank you for your donation of KES {payment.amount}.'

                        )

                        

                    else:  # Failed

                        payment.status = 'failed'

                        payment.mark_failed()

                        

                        # Create failure notification

                        Notification.objects.create(

                            user=payment.donation.donor,

                            notification_type='system',

                            message=f'M-Pesa payment failed: {result_desc}. Please try again or contact support.'

                        )

                

                except PaymentTransaction.DoesNotExist:

                    pass  # Transaction not found

            

            return HttpResponse('OK')

            

        except Exception as e:

            print(f"M-Pesa callback error: {e}")

            return HttpResponse('ERROR', status=500)

    

    return HttpResponse('Method not allowed', status=405)

def accept_donation(request, donation_id):

    # Ensure only the foodbank that owns the donation can accept it

    donation = get_object_or_404(

        Donation,

        id=donation_id,

        foodbank=request.user.foodbank_profile

    )



    # Prevent re-accepting

    if donation.status == 'accepted':

        messages.warning(request, "This donation has already been accepted.")

        return _redirect_back_or_default(request, 'foodbank_donations_list')



    # Mark donation accepted

    donation.status = 'accepted'

    update_fields = ['status']

    if donation.foodbank_request_id is not None and donation.accepted_by_recipient_id is not None:

        donation.accepted_by_recipient = None

        update_fields.append('accepted_by_recipient')

    donation.save(update_fields=update_fields)



    # If this donation is linked to a foodbank_request, try to update the original recipient request

    if donation.foodbank_request:

        # Try a few common attribute names that might point to the recipient's request

        original_req = (

            getattr(donation.foodbank_request, 'original_request', None)

            or getattr(donation.foodbank_request, 'linked_recipient_request', None)

            or getattr(donation.foodbank_request, 'recipient_request', None)

            or getattr(donation.foodbank_request, 'linked_request_management', None)

        )



        if not original_req and hasattr(donation.foodbank_request, 'recipient_requests'):

            original_req = donation.foodbank_request.recipient_requests.order_by('-time_of_request').first()



        if original_req:

            try:

                # Use atomic update to avoid partial writes

                from django.db import transaction

                with transaction.atomic():

                    if hasattr(original_req, 'acknowledged_by_recipient'):

                        original_req.acknowledged_by_recipient = False

                    if hasattr(original_req, 'acknowledged_at'):

                        original_req.acknowledged_at = None

                    if hasattr(original_req, 'acknowledged_by_recipient') or hasattr(original_req, 'acknowledged_at'):

                        ack_update_fields = []

                        if hasattr(original_req, 'acknowledged_by_recipient'):

                            ack_update_fields.append('acknowledged_by_recipient')

                        if hasattr(original_req, 'acknowledged_at'):

                            ack_update_fields.append('acknowledged_at')

                        if ack_update_fields:

                            original_req.save(update_fields=ack_update_fields)



                    # ITEM-based request handling (quantity) - only for item/subsidized donations, NOT monetary

                    donated_qty = None

                    if donation.donation_type == 'subsidized':

                        donated_qty = donation.subsidized_quantity or donation.quantity

                    elif donation.donation_type == 'item':

                        donated_qty = donation.quantity



                    if donated_qty is None and donation.foodbank_request and getattr(donation.foodbank_request, 'quantity_needed', None):

                        donated_qty = donation.foodbank_request.quantity_needed



                    if donation.donation_type in ['item', 'subsidized'] and donated_qty is not None and getattr(original_req, 'quantity', None) is not None:

                        donated_qty = int(donated_qty or 0)

                        fulfilled = int(getattr(original_req, 'quantity_fulfilled', 0) or 0)

                        needed = int(getattr(original_req, 'quantity', 0) or 0)

                        remaining = needed - fulfilled



                        if donated_qty > 0 and remaining > 0:

                            use = min(donated_qty, remaining)

                            original_req.quantity_fulfilled = fulfilled + use



                            if original_req.quantity_fulfilled >= needed:

                                original_req.status = 'awaiting_recipient'

                            else:

                                original_req.status = 'partial'



                            # ðŸ”‘ CRITICAL RESET

                            if hasattr(original_req, 'acknowledged_by_recipient'):

                                original_req.acknowledged_by_recipient = False

                            if hasattr(original_req, 'acknowledged_at'):

                                original_req.acknowledged_at = None



                            original_req.save()





                            # Notify recipient with clear message depending on partial vs full coverage

                            if original_req.status == 'partial':

                                Notification.objects.create(

                                    user=original_req.recipient.user,

                                    message=(

                                        f"Good news â€” {use} {getattr(original_req,'quantity_unit', '')} "

                                        f"has been allocated for your request '{getattr(original_req, 'description', original_req.id)}'. "

                                        f"Status: Partially fulfilled ({original_req.quantity_fulfilled}/{original_req.quantity})."

                                    )

                                )

                            else:

                                Notification.objects.create(

                                    user=original_req.recipient.user,

                                    notification_type='donation_received',

                                    message=(

                                        f"A donation covering your request '{getattr(original_req, 'description', original_req.id)}' "

                                        f"is ready. Please acknowledge receipt so we can mark the request as fulfilled."

                                    )

                                )



                    # MONEY-based request handling (amount)

                    elif getattr(donation, 'amount', None) is not None and getattr(original_req, 'amount_needed', None) is not None:

                        donated_amount = float(donation.amount or 0)

                        received = float(getattr(original_req, 'amount_received', 0) or 0)

                        needed_amount = float(getattr(original_req, 'amount_needed', 0) or 0)

                        remaining_amount = needed_amount - received



                        if donated_amount > 0 and remaining_amount > 0:

                            use_amount = min(donated_amount, remaining_amount)

                            original_req.amount_received = received + use_amount



                            if original_req.amount_received >= needed_amount:

                                original_req.status = 'awaiting_recipient'

                            else:

                                original_req.status = 'partial'



                            original_req.save()



                            if original_req.status == 'partial':

                                Notification.objects.create(

                                    user=original_req.recipient.user,

                                    message=(

                                        f"Partial monetary contribution received for your request '{getattr(original_req, 'description', original_req.id)}': "

                                        f"KSH {original_req.amount_received}/{original_req.amount_needed}."

                                    )

                                )

                            else:

                                Notification.objects.create(

                                    user=original_req.recipient.user,

                                    notification_type='donation_received',

                                    message=(

                                        f"A monetary donation covering your request '{getattr(original_req, 'description', original_req.id)}' is ready. "

                                        "Please acknowledge receipt to complete the process."

                                    )

                                )

                    # MONETARY donation to a quantity-based request: add the quantity this money is "for" to quantity_fulfilled

                    elif donation.donation_type == 'money' and getattr(donation, 'amount', None) is not None:

                        # Quantity this monetary donation is for (e.g. "KES 500 for 50 kg" -> 50)
                        qty_for_money = None
                        if donation.foodbank_request and getattr(donation.foodbank_request, 'quantity_needed', None):
                            qty_for_money = int(donation.foodbank_request.quantity_needed or 0)

                        if qty_for_money is not None and qty_for_money > 0 and getattr(original_req, 'quantity', None) is not None:
                            # Quantity-based request: add fulfilled amount so partial + monetary can become fulfilled
                            fulfilled = int(getattr(original_req, 'quantity_fulfilled', 0) or 0)
                            needed = int(getattr(original_req, 'quantity', 0) or 0)
                            remaining = needed - fulfilled
                            if remaining > 0:
                                use = min(qty_for_money, remaining)
                                original_req.quantity_fulfilled = fulfilled + use
                                if original_req.quantity_fulfilled >= needed:
                                    original_req.status = 'awaiting_recipient'
                                else:
                                    original_req.status = 'partial'
                                if hasattr(original_req, 'acknowledged_by_recipient'):
                                    original_req.acknowledged_by_recipient = False
                                if hasattr(original_req, 'acknowledged_at'):
                                    original_req.acknowledged_at = None
                                original_req.save()
                                if original_req.status == 'partial':
                                    Notification.objects.create(
                                        user=original_req.recipient.user,
                                        message=(
                                            f"Monetary donation received. Request partially fulfilled: "
                                            f"{original_req.quantity_fulfilled}/{original_req.quantity}."
                                        )
                                    )
                                else:
                                    Notification.objects.create(
                                        user=original_req.recipient.user,
                                        notification_type='donation_received',
                                        message=(
                                            f"A monetary donation covering your request '{getattr(original_req, 'description', original_req.id)}' "
                                            "is ready. Please acknowledge receipt to complete the process."
                                        )
                                    )
                            else:
                                if getattr(original_req, 'status', '') not in ['fulfilled', 'awaiting_recipient']:
                                    original_req.status = 'awaiting_recipient'
                                    original_req.save()
                                Notification.objects.create(
                                    user=original_req.recipient.user,
                                    notification_type='donation_received',
                                    message=f"A monetary donation of KES {donation.amount} has been received for your request '{getattr(original_req, 'description', original_req.id)}'. Please acknowledge receipt."
                                )
                        else:
                            # No quantity_needed on foodbank request or non-quantity request: just mark as received
                            if getattr(original_req, 'status', '') not in ['fulfilled', 'awaiting_recipient']:
                                original_req.status = 'awaiting_recipient'
                                original_req.save()
                            Notification.objects.create(
                                user=original_req.recipient.user,
                                notification_type='donation_received',
                                message=f"A monetary donation of KES {donation.amount} has been received for your request '{getattr(original_req, 'description', original_req.id)}'. Please acknowledge receipt."
                            )

                    else:

                        # Unknown request shape - mark as awaiting_recipient if not already fulfilled

                        if getattr(original_req, 'status', '') not in ['fulfilled', 'awaiting_recipient']:

                            original_req.status = 'awaiting_recipient'

                            original_req.save()

                            Notification.objects.create(

                                user=original_req.recipient.user,

                                notification_type='donation_received',

                                message=f"A donation for your request '{getattr(original_req, 'description', original_req.id)}' is ready. Please acknowledge receipt."

                            )

            except Exception as e:

                # Log but don't break flow

                print(f"Error updating original request on accept_donation: {e}")



    messages.success(request, "Donation accepted and request updated!")

    return _redirect_back_or_default(request, 'foodbank_requests_view')

def decline_donation(request, donation_id):

    donation = get_object_or_404(

        Donation,

        id=donation_id,

        foodbank=request.user.foodbank_profile

    )



    if request.method == 'POST':

        donation.status = 'declined'

        donation.decline_message = request.POST.get('message', '').strip()

        donation.save(update_fields=['status', 'decline_message'])



        foodbank_request = donation.foodbank_request



        # ðŸ”— Find the original recipient request safely

        request_obj = (

            getattr(foodbank_request, 'original_request', None)

            or getattr(foodbank_request, 'linked_recipient_request', None)

            or getattr(foodbank_request, 'recipient_request', None)

        )



        if request_obj:

            # Check if any non-declined donations remain

            remaining_donations = foodbank_request.donations.exclude(status='declined')



            if not remaining_donations.exists():

                update_fields = ['status']

                if getattr(request_obj, 'quantity_fulfilled', 0) > 0:

                    request_obj.status = 'partial'

                else:

                    request_obj.status = 'declined'



                if hasattr(request_obj, 'decline_message'):

                    request_obj.decline_message = donation.decline_message

                    update_fields.append('decline_message')



                # Track that the foodbank performed this update so recipients can mask the status

                if hasattr(request_obj, 'updated_by'):

                    request_obj.updated_by = request.user

                    update_fields.append('updated_by')



                request_obj.save(update_fields=update_fields)



        messages.warning(request, "Donation declined.")



    return _redirect_back_or_default(request, 'foodbank_requests_view')

def _get_request_unit_label(request_obj):
    """Resolve the human-readable unit label for FoodBankRequest/RequestManagement objects."""
    if not request_obj:
        return ''

    custom_unit = getattr(request_obj, 'custom_unit', None)

    quantity_unit = getattr(request_obj, 'quantity_unit', None)
    if quantity_unit:
        if quantity_unit == 'other' and custom_unit:
            return custom_unit
        try:
            return request_obj.get_quantity_unit_display()
        except Exception:
            return quantity_unit

    unit_field = getattr(request_obj, 'unit', None)
    if unit_field:
        if unit_field == 'other' and custom_unit:
            return custom_unit
        try:
            return request_obj.get_unit_display()
        except Exception:
            return unit_field

    if custom_unit:
        return custom_unit

    linked_req = getattr(request_obj, 'linked_request_management', None)
    if linked_req:
        return _get_request_unit_label(linked_req)

    return ''

def select_foodbank_for_donation(request):

    if request.user.user_type != 'DONOR':
        messages.error(request, 'Only donors can make donations.')
        return redirect('dashboard')

    foodbanks = FoodBankProfile.objects.select_related('user').filter(
        is_approved='approved',
        user__is_active=True
    )

    # Service type filter
    service_type = (request.GET.get('service_type') or '').strip()
    if service_type in {'food', 'non_food', 'both'}:
        foodbanks = foodbanks.filter(service_type=service_type)

    # Location search
    location = (request.GET.get('location') or '').strip()
    if location:
        foodbanks = foodbanks.filter(address__icontains=location)

    # Food bank name search
    foodbank_name = (request.GET.get('foodbank_name') or '').strip()
    if foodbank_name:
        foodbanks = foodbanks.filter(foodbank_name__icontains=foodbank_name)

    # Date joined range filter
    date_from_raw = (request.GET.get('date_from') or '').strip()
    date_to_raw = (request.GET.get('date_to') or '').strip()
    date_from_value = None
    date_to_value = None

    if date_from_raw:
        try:
            date_from_value = datetime.strptime(date_from_raw, '%Y-%m-%d').date()
        except ValueError:
            messages.warning(request, 'Invalid "From" date. Please use YYYY-MM-DD.')

    if date_to_raw:
        try:
            date_to_value = datetime.strptime(date_to_raw, '%Y-%m-%d').date()
        except ValueError:
            messages.warning(request, 'Invalid "To" date. Please use YYYY-MM-DD.')

    if date_from_value and date_to_value and date_from_value > date_to_value:
        messages.warning(request, '"From" date cannot be later than "To" date.')
    else:
        if date_from_value:
            foodbanks = foodbanks.filter(user__date_joined__date__gte=date_from_value)
        if date_to_value:
            foodbanks = foodbanks.filter(user__date_joined__date__lte=date_to_value)

    # Sorting
    sort = (request.GET.get('sort') or 'newest').strip()
    if sort == 'oldest':
        foodbanks = foodbanks.order_by('user__date_joined', 'foodbank_name')
    else:
        foodbanks = foodbanks.order_by('-user__date_joined', 'foodbank_name')

    context = {
        'foodbanks': foodbanks,
    }
    return render(request, 'donor/select_foodbank.html', context)
