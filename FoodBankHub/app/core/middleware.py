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
