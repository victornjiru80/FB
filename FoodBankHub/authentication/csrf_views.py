"""
Custom CSRF failure view for FoodBankHub
"""
from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token
from django.http import HttpResponseForbidden
import logging

logger = logging.getLogger(__name__)

@requires_csrf_token
def csrf_failure(request, reason=""):
    """
    Custom CSRF failure view that provides a user-friendly error page
    instead of the default Django CSRF error page.
    
    Args:
        request: The HTTP request object
        reason: The reason for CSRF failure (provided by Django)
    
    Returns:
        HttpResponseForbidden with custom template
    """
    
    # Log the CSRF failure for security monitoring
    logger.warning(
        f"CSRF failure for user {request.user if request.user.is_authenticated else 'Anonymous'} "
        f"from IP {request.META.get('REMOTE_ADDR', 'Unknown')}. "
        f"Reason: {reason}. "
        f"Referer: {request.META.get('HTTP_REFERER', 'None')}. "
        f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'None')}"
    )
    
    # Prepare context for the template
    context = {
        'reason': reason,
        'request_path': request.path,
        'referer': request.META.get('HTTP_REFERER', ''),
        'user_authenticated': request.user.is_authenticated,
    }
    
    # Render the custom CSRF failure template with 403 status
    response = render(request, 'errors/csrf_failure.html', context)
    response.status_code = 403
    
    return response


def csrf_failure_ajax(request, reason=""):
    """
    CSRF failure handler for AJAX requests
    Returns JSON response instead of HTML
    """
    from django.http import JsonResponse
    
    logger.warning(
        f"CSRF failure (AJAX) for user {request.user if request.user.is_authenticated else 'Anonymous'} "
        f"from IP {request.META.get('REMOTE_ADDR', 'Unknown')}. "
        f"Reason: {reason}"
    )
    
    return JsonResponse({
        'error': 'CSRF verification failed',
        'message': 'Security verification failed. Please refresh the page and try again.',
        'code': 'csrf_failure',
        'reload_required': True
    }, status=403)


def custom_404_handler(request, exception):
    """
    Custom 404 error handler that works in both DEBUG and production modes
    """
    logger.info(
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


def custom_403_handler(request, exception):
    """
    Custom 403 error handler for permission denied scenarios
    """
    logger.warning(
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


def custom_500_handler(request):
    """
    Custom 500 error handler for server errors
    """
    logger.error(
        f"500 error for path '{request.path}' from IP {request.META.get('REMOTE_ADDR', 'Unknown')}. "
        f"User: {request.user if request.user.is_authenticated else 'Anonymous'}"
    )
    
    # Use a simple context since we can't rely on complex template inheritance in error scenarios
    context = {
        'request_path': request.path,
    }
    
    response = render(request, '500.html', context)
    response.status_code = 500
    return response
