from django.contrib.auth import logout
from django.shortcuts import redirect
from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
import time
import logging


class SimpleSessionTimeoutMiddleware:
    """
    Simple middleware to handle session timeout functionality.
    Automatically logs out users after a period of inactivity.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip session timeout for unauthenticated users
        if not request.user.is_authenticated:
            response = self.get_response(request)
            return response

        # Skip session timeout for certain URLs (login, logout, etc.)
        exempt_urls = ['/login/', '/logout/', '/admin/']
        
        # Check if current path should be exempt from timeout
        current_path = request.path
        if any(current_path.startswith(url) for url in exempt_urls):
            response = self.get_response(request)
            return response

        # Get session timeout settings
        session_timeout = getattr(settings, 'SESSION_COOKIE_AGE', 600)  # Default 10 minutes
        
        # Get the last activity time from session
        last_activity = request.session.get('last_activity')
        current_time = time.time()
        
        if last_activity:
            # Check if session has expired
            if current_time - last_activity > session_timeout:
                # Session has expired, log out the user
                logout(request)
                messages.info(request, 'Your session has expired due to inactivity. Please log in again.')
                return redirect('login')
        
        # Update last activity time
        request.session['last_activity'] = current_time
            
        response = self.get_response(request)
        return response


class CustomErrorHandlerMiddleware:
    """
    Middleware to handle custom error pages in development mode
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger(__name__)

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Handle exceptions and return custom error pages
        """
        if isinstance(exception, Http404):
            return self.handle_404(request, exception)
        elif isinstance(exception, PermissionDenied):
            return self.handle_403(request, exception)
        
        # Let Django handle other exceptions normally
        return None

    def handle_404(self, request, exception):
        """Handle 404 errors with custom template"""
        self.logger.info(
            f"404 error for path '{request.path}' from IP {request.META.get('REMOTE_ADDR', 'Unknown')}. "
            f"User: {request.user if request.user.is_authenticated else 'Anonymous'}. "
            f"Referer: {request.META.get('HTTP_REFERER', 'None')}"
        )
        
        context = {
            'request_path': request.path,
            'exception': str(exception) if exception else 'Page not found',
        }
        
        response = render(request, '404.html', context)
        response.status_code = 404
        return response

    def handle_403(self, request, exception):
        """Handle 403 errors with custom template"""
        self.logger.warning(
            f"403 error for path '{request.path}' from IP {request.META.get('REMOTE_ADDR', 'Unknown')}. "
            f"User: {request.user if request.user.is_authenticated else 'Anonymous'}. "
            f"Exception: {exception}"
        )
        
        context = {
            'request_path': request.path,
            'exception': str(exception) if exception else 'Access forbidden',
        }
        
        response = render(request, '403.html', context)
        response.status_code = 403
        return response


class FoodBankProfileCompletionMiddleware:
    """
    Prevent food banks from performing transactional actions until profile is 100% complete.

    We keep read-only pages accessible, but block:
    - POST/PUT/PATCH/DELETE requests (transactions)
    - key transaction entry pages (subscribe/payment, inventory/manage-requests, create/edit requests)
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Allow these endpoints even when profile incomplete
        self.allowed_url_names = {
            'logout',
            'login',
            'dashboard',
            'home',
            'foodbank_settings',
            'update_foodbank_profile',
            'change_foodbank_password',
            'manage_foodbank_profile',
            'foodbank_public_profile',
        }

        # Block these entry points even on GET (they lead to transactions)
        self.blocked_entry_url_names = {
            'create_foodbank_request',
            'edit_foodbank_request',
            'delete_foodbank_request',
            'fulfill_foodbank_request',
            'foodbank_inventory',
            'foodbank_requests_view',
            'allocate_donation',
            'decline_donation',
            'decline_request',
            'accept_request',
            'fulfill_recipient_request',
            'mark_request_completed',
            'mark_received',
            'manage_subscription',
            'subscribe',
            'payment_detail_foodbank',
        }

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        try:
            user_type = getattr(request.user, 'user_type', None)
        except Exception:
            user_type = None

        if (user_type or '').upper() != 'FOODBANK':
            return self.get_response(request)

        # Determine completion
        completion = 0
        try:
            foodbank_profile = getattr(request.user, 'foodbank_profile', None)
            if foodbank_profile:
                completion = int(foodbank_profile.get_profile_completion_percentage() or 0)
        except Exception:
            completion = 0

        if completion >= 100:
            return self.get_response(request)

        url_name = None
        try:
            match = getattr(request, 'resolver_match', None)
            url_name = getattr(match, 'url_name', None)
        except Exception:
            url_name = None

        # Always allow static/media and admin
        if request.path.startswith('/static/') or request.path.startswith('/media/') or request.path.startswith('/admin/'):
            return self.get_response(request)

        if url_name in self.allowed_url_names:
            return self.get_response(request)

        # Block all mutating requests unless explicitly allowed
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            messages.warning(
                request,
                'Please complete your Food Bank profile to 100% before performing transactions.',
            )
            return redirect('manage_foodbank_profile')

        # Block entry points to transactional pages even on GET
        if url_name in self.blocked_entry_url_names:
            messages.warning(
                request,
                'Please complete your Food Bank profile to 100% before accessing transaction features.',
            )
            return redirect('manage_foodbank_profile')

        return self.get_response(request)
