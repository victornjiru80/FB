from django import template
from decimal import Decimal

register = template.Library()


@register.filter(name='neutral_status_unspecified')
def neutral_status_unspecified(item):
    """Map UnspecifiedDonationManagement status to neutral label."""
    from custom_admin.utils import get_neutral_status
    fb = getattr(item, 'foodbank_status', '')
    rec = getattr(item, 'recipient_status', '')
    return get_neutral_status('unspecified', fb, {'foodbank_status': fb, 'recipient_status': rec})


@register.filter(name='neutral_status_subsidized')
def neutral_status_subsidized(donation):
    """Map subsidized Donation status to neutral label."""
    from custom_admin.utils import get_neutral_status
    ctx = {
        'accepted_by_recipient': getattr(donation, 'accepted_by_recipient', None),
        'declined_by_recipient': getattr(donation, 'declined_by_recipient', None),
        'delivery_status': getattr(donation, 'delivery_status', ''),
    }
    return get_neutral_status('subsidized', getattr(donation, 'status', ''), ctx)


@register.filter(name='neutral_status_direct')
def neutral_status_direct(fb_request):
    """Map FoodBankRequest status_label to neutral label."""
    from custom_admin.utils import get_neutral_status
    label = getattr(fb_request, 'status_label', None) or getattr(fb_request, 'get_status_display', lambda: '')()
    if callable(label):
        label = label()
    return get_neutral_status('direct', str(label).lower() if label else '', {})


@register.filter(name='neutral_status_specified')
def neutral_status_specified(req):
    """Map RequestManagement status to neutral label."""
    from custom_admin.utils import get_neutral_status
    status = getattr(req, 'status', '')
    ctx = {'request_obj': req}
    return get_neutral_status('specified', str(status).lower() if status else '', ctx)


@register.filter(name='calculate_discount')
def calculate_discount(donation):
    """
    Calculate discount percentage from market price and subsidized price
    Formula: ((market_price - subsidized_price) / market_price) * 100
    """
    try:
        if donation.subsidized_market_price and donation.subsidized_price:
            market_price = Decimal(str(donation.subsidized_market_price))
            subsidized_price = Decimal(str(donation.subsidized_price))
            
            if market_price > 0:
                discount = ((market_price - subsidized_price) / market_price) * 100
                return f"{discount:.1f}"
        return "0.0"
    except (AttributeError, ValueError, TypeError, ZeroDivisionError):
        return "0.0"
