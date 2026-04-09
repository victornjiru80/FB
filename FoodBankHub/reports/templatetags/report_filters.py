from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def calculate_discount(market_price, subsidized_price):
    """Calculate discount percentage from market price and subsidized price"""
    try:
        market = Decimal(str(market_price)) if market_price else Decimal('0')
        subsidized = Decimal(str(subsidized_price)) if subsidized_price else Decimal('0')
        
        if market > 0 and subsidized >= 0:
            discount = ((market - subsidized) / market) * 100
            return round(discount, 0)
        return None
    except (ValueError, TypeError, ZeroDivisionError):
        return None
