from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.urls import reverse


def staff_member_required(view_func):
    """
    Decorator for views that checks user is logged in and is staff,
    redirecting to the main login page if needed.
    """
    def check_staff(user):
        return user.is_authenticated and user.is_staff

    actual_decorator = user_passes_test(
        check_staff,
        login_url='login',
        redirect_field_name='next'
    )

    return actual_decorator(view_func)


def admin_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is staff,
    redirecting to the main login page if necessary.
    """
    def check_admin(user):
        return user.is_authenticated and user.is_staff
    
    actual_decorator = user_passes_test(
        check_admin,
        login_url='login',
        redirect_field_name='next'
    )
    
    return actual_decorator(view_func)


def superuser_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is a superuser,
    redirecting to the main login page if necessary.
    """
    def check_superuser(user):
        return user.is_authenticated and user.is_superuser
    
    actual_decorator = user_passes_test(
        check_superuser,
        login_url='login',
        redirect_field_name='next'
    )
    
    return actual_decorator(view_func)
