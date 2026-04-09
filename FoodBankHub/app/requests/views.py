"""
Requests module views (trimmed).

Keeps only request-related endpoints referenced by `app/requests/urls.py`.
Implementation delegates to the working monolith (`authentication.views`) to keep
current behavior unchanged while the future modular architecture stays clean.
"""

from authentication.views import (
    create_foodbank_request,
    edit_foodbank_request,
    delete_foodbank_request,
    fulfill_foodbank_request,
    create_request,
    recipient_requests_view,
    export_recipient_requests,
    request_detail,
    fulfill_request,
    partial_fulfill_request,
    decline_request,
)

