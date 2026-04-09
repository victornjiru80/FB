from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


def donor_required(view_func):
    """
    Decorator to check if user is a donor.
    Redirects to dashboard if not a donor.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        if request.user.user_type != 'DONOR':
            messages.error(request, 'This page is only accessible to donors.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def foodbank_required(view_func):
    """
    Decorator to check if user is a food bank.
    Redirects to dashboard if not a food bank.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        if request.user.user_type != 'FOODBANK':
            messages.error(request, 'This page is only accessible to food banks.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def subscription_required(view_func):
    """
    Decorator to check if food bank has active subscription or trial.
    Redirects to subscription page if access is not allowed.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Only apply to food bank users
        if request.user.is_authenticated and request.user.user_type == 'FOODBANK':
            try:
                foodbank_profile = request.user.foodbank_profile
                subscription = foodbank_profile.subscription
                
                # Check if subscription allows access
                if not subscription.can_access_features():
                    messages.warning(
                        request, 
                        'Your trial has expired. Please subscribe to continue using the platform.'
                    )
                    return redirect('authentication:subscription_status')
            except Exception as e:
                # If no subscription exists, redirect to subscription page
                messages.error(
                    request, 
                    'Please set up your subscription to access this feature.'
                )
                return redirect('authentication:subscription_status')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def trial_or_subscription_required(view_func):
    """
    Alternative decorator with custom message.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == 'FOODBANK':
            try:
                subscription = request.user.foodbank_profile.subscription
                if not subscription.can_access_features():
                    messages.warning(
                        request,
                        f'This feature requires an active subscription. Your {subscription.get_status_display()} has ended.'
                    )
                    return redirect('authentication:subscription_status')
            except:
                messages.error(request, 'Subscription information not found.')
                return redirect('authentication:subscription_status')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
