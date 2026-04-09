from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging
import threading

# Set up logger
logger = logging.getLogger(__name__)

def send_welcome_email(user, user_type):
    """
    Send a personalized welcome email to new users based on their type.
    
    Args:
        user: The CustomUser instance
        user_type: The type of user (DONOR, FOODBANK, RECIPIENT)
    """
    try:
        subject = 'Welcome to FoodBank Hub!'
        
        # Select appropriate template based on user type
        if user_type == 'DONOR':
            template = 'authentication/emails/welcome_donor.html'
        elif user_type == 'FOODBANK':
            template = 'authentication/emails/welcome_foodbank.html'
        elif user_type == 'RECIPIENT':
            template = 'authentication/emails/welcome_recipient.html'
        else:
            template = 'authentication/emails/welcome_generic.html'

        # Render the email template with user context
        message = render_to_string(template, {
            'user': user,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000')
        })
        
        # Send the email
        result = send_mail(
            subject,
            '',  # Empty plain text, HTML will be used
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False,  # Changed to False to catch errors
        )
        
        if result:
            logger.info(f"Welcome email sent successfully to {user.email} ({user_type})")
        else:
            logger.warning(f"Failed to send welcome email to {user.email} ({user_type})")
            
    except Exception as e:
        logger.error(f"Error sending welcome email to {user.email} ({user_type}): {str(e)}")
        raise  # Re-raise the exception for proper handling 


def _send_donation_confirmation_email_impl(donation):
    """Internal: render and send donation confirmation email. Used by sync and async senders."""
    subject = 'Thank You for Your Donation - FoodBank Hub'
    template = 'authentication/emails/donation_confirmation.html'
    message = render_to_string(template, {
        'donation': donation,
        'donor': donation.donor,
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000')
    })
    result = send_mail(
        subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [donation.donor.email],
        html_message=message,
        fail_silently=False,
    )
    if result:
        logger.info(f"Donation confirmation email sent successfully to {donation.donor.email}")
    else:
        logger.warning(f"Failed to send donation confirmation email to {donation.donor.email}")


def send_donation_confirmation_email(donation):
    """
    Send a confirmation email to the donor after they make a donation (synchronous).
    For request handlers, prefer send_donation_confirmation_email_async to avoid blocking.
    """
    try:
        _send_donation_confirmation_email_impl(donation)
    except Exception as e:
        logger.error(f"Error sending donation confirmation email to {donation.donor.email}: {str(e)}")
        raise


def send_donation_confirmation_email_async(donation):
    """
    Send the donation confirmation email in a background thread so the HTTP response
    is not delayed by SMTP. Failures are logged only.
    """
    donation_id = donation.pk
    if not donation_id:
        logger.warning("Cannot send donation confirmation email asynchronously: donation has no pk yet.")
        return

    def _send_in_thread():
        try:
            from django.db import connection
            connection.close()  # release request thread's connection
            from .models import Donation
            donation = Donation.objects.select_related('donor', 'foodbank').get(pk=donation_id)
            _send_donation_confirmation_email_impl(donation)
        except Exception as e:
            logger.error(f"Error sending donation confirmation email (async, donation_id={donation_id}): {str(e)}")

    thread = threading.Thread(target=_send_in_thread, daemon=True)
    thread.start()


def send_foodbank_request_notification_email(request, donors):
    """
    Send notification emails to donors about new food bank requests.
    
    Args:
        request: The FoodBankRequest instance
        donors: QuerySet or list of donors to notify
    """
    try:
        subject = f'Help Needed: {request.title} - FoodBank Hub'
        template = 'authentication/emails/foodbank_request_notification.html'
        
        successful_sends = 0
        failed_sends = 0
        
        for donor in donors:
            try:
                # Render the email template with request and donor context
                message = render_to_string(template, {
                    'request': request,
                    'donor': donor,
                    'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000')
                })
                
                # Send the email
                result = send_mail(
                    subject,
                    '',  # Empty plain text, HTML will be used
                    settings.DEFAULT_FROM_EMAIL,
                    [donor.email],
                    html_message=message,
                    fail_silently=False,
                )
                
                if result:
                    successful_sends += 1
                    logger.info(f"Food bank request notification sent to {donor.email}")
                else:
                    failed_sends += 1
                    logger.warning(f"Failed to send food bank request notification to {donor.email}")
                    
            except Exception as e:
                failed_sends += 1
                logger.error(f"Error sending food bank request notification to {donor.email}: {str(e)}")
                
        logger.info(f"Food bank request notifications: {successful_sends} successful, {failed_sends} failed")
        return successful_sends, failed_sends
        
    except Exception as e:
        logger.error(f"Error in send_foodbank_request_notification_email: {str(e)}")
        raise


def send_urgent_request_notification_email(request, donors):
    """
    Send urgent notification emails to donors about high-priority food bank requests.
    
    Args:
        request: The FoodBankRequest instance (should be urgent/high priority)
        donors: QuerySet or list of donors to notify
    """
    try:
        subject = f' URGENT: {request.title} - Immediate Help Needed'
        template = 'authentication/emails/foodbank_request_notification.html'
        
        successful_sends = 0
        failed_sends = 0
        
        for donor in donors:
            try:
                # Render the email template with request and donor context
                message = render_to_string(template, {
                    'request': request,
                    'donor': donor,
                    'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
                    'is_urgent': True
                })
                
                # Send the email
                result = send_mail(
                    subject,
                    '',  # Empty plain text, HTML will be used
                    settings.DEFAULT_FROM_EMAIL,
                    [donor.email],
                    html_message=message,
                    fail_silently=False,
                )
                
                if result:
                    successful_sends += 1
                    logger.info(f"Urgent request notification sent to {donor.email}")
                else:
                    failed_sends += 1
                    logger.warning(f"Failed to send urgent request notification to {donor.email}")
                    
            except Exception as e:
                failed_sends += 1
                logger.error(f"Error sending urgent request notification to {donor.email}: {str(e)}")
                
        logger.info(f"Urgent request notifications: {successful_sends} successful, {failed_sends} failed")
        return successful_sends, failed_sends
        
    except Exception as e:
        logger.error(f"Error in send_urgent_request_notification_email: {str(e)}")
        raise


def send_application_received_email(user):
    """
    Send confirmation to a newly registered food bank that their application
    has been received and is pending review.
    """
    try:
        foodbank_name = getattr(getattr(user, "foodbank_profile", None), "foodbank_name", "your food bank")
        subject = "FoodBank Hub Application Received"
        message = (
            f"Hello {foodbank_name},\n\n"
            "Thank you for registering with FoodBank Hub.\n"
            "We have received your application and it is currently under review.\n\n"
            "You will receive another email once your application is approved or if we need more information.\n\n"
            "Best regards,\n"
            "FoodBank Hub Team"
        )

        result = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        if result:
            logger.info(f"Application received email sent successfully to {user.email}")
        else:
            logger.warning(f"Failed to send application received email to {user.email}")

        return result
    except Exception as e:
        logger.error(f"Error sending application received email to {user.email}: {str(e)}")
        raise


def notify_admins_new_application(foodbank_profile):
    """
    Notify active admins that a new food bank application has been submitted.
    """
    try:
        from .models import CustomUser

        admin_emails = list(
            CustomUser.objects.filter(
                user_type='ADMIN',
                is_active=True,
            ).exclude(email='').values_list('email', flat=True).distinct()
        )

        if not admin_emails:
            logger.warning("No active admin emails found for new application notification.")
            return 0

        subject = f"New Food Bank Application: {foodbank_profile.foodbank_name}"
        message = (
            "A new food bank application has been submitted.\n\n"
            f"Food Bank: {foodbank_profile.foodbank_name}\n"
            f"Contact Person: {foodbank_profile.contact_person}\n"
            f"Email: {foodbank_profile.user.email}\n"
            f"Phone: {foodbank_profile.user.phone_number}\n"
            f"Address: {foodbank_profile.address or 'Not provided'}\n\n"
            "Please log in to the admin panel to review and process this application."
        )

        result = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            admin_emails,
            fail_silently=False,
        )

        if result:
            logger.info(
                f"Admin notification sent for food bank application {foodbank_profile.id} "
                f"to {len(admin_emails)} admin(s)"
            )
        else:
            logger.warning(
                f"Failed to send admin notification for food bank application {foodbank_profile.id}"
            )

        return result
    except Exception as e:
        logger.error(
            f"Error notifying admins for food bank application {foodbank_profile.id}: {str(e)}"
        )
        raise


def send_approval_email(user):
    """
    Send approval email when a food bank application is approved.
    """
    try:
        foodbank_name = getattr(getattr(user, "foodbank_profile", None), "foodbank_name", "your food bank")
        subject = "Your FoodBank Hub Application Has Been Approved"
        message = (
            f"Hello {foodbank_name},\n\n"
            "Great news. Your food bank application has been approved.\n"
            "Your account is now active and you can log in to start using FoodBank Hub.\n\n"
            "Best regards,\n"
            "FoodBank Hub Team"
        )

        result = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        if result:
            logger.info(f"Approval email sent successfully to {user.email}")
        else:
            logger.warning(f"Failed to send approval email to {user.email}")

        return result
    except Exception as e:
        logger.error(f"Error sending approval email to {user.email}: {str(e)}")
        raise


def send_rejection_email(user, rejection_reason):
    """
    Send rejection email when a food bank application is rejected.
    """
    try:
        foodbank_name = getattr(getattr(user, "foodbank_profile", None), "foodbank_name", "your food bank")
        subject = "Update on Your FoodBank Hub Application"
        message = (
            f"Hello {foodbank_name},\n\n"
            "We reviewed your food bank application and are unable to approve it at this time.\n\n"
            f"Reason: {rejection_reason}\n\n"
            "You may update your details and reapply, or contact support for clarification.\n\n"
            "Best regards,\n"
            "FoodBank Hub Team"
        )

        result = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        if result:
            logger.info(f"Rejection email sent successfully to {user.email}")
        else:
            logger.warning(f"Failed to send rejection email to {user.email}")

        return result
    except Exception as e:
        logger.error(f"Error sending rejection email to {user.email}: {str(e)}")
        raise
