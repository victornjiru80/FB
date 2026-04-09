from django.urls import path
from . import views

# Subscription-focused snapshot routes for future module activation.
urlpatterns = [
    path('subscription/manage/', views.manage_subscription, name='manage_subscription'),
    path('subscription/status/', views.subscription_status, name='subscription_status'),
    path('subscription/requests/', views.subscription_requests, name='subscription_requests'),
    path('subscription/status/export/excel/', views.export_subscription_payments_excel, name='subscription_payments_export_excel'),
    path('subscription/status/export/pdf/', views.export_subscription_payments_pdf, name='subscription_payments_export_pdf'),
    path('subscription/subscribe/', views.subscribe, name='subscribe'),
    path('subscription/payment/<int:payment_id>/', views.payment_detail, name='payment_detail_foodbank'),
    path('subscription/info/', views.subscription_info, name='subscription_info'),
]
