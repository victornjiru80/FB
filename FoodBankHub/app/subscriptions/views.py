"""
Subscriptions module views (trimmed).
"""

from authentication.subscription_views import (
    manage_subscription,
    subscription_status,
    subscription_requests,
    export_subscription_payments_excel,
    export_subscription_payments_pdf,
    subscribe,
    payment_detail,
    subscription_info,
)

# Keep the url-name compatibility from monolith urls.py
payment_detail_foodbank = payment_detail

