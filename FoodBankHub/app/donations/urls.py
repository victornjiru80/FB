from django.urls import path
from . import views

# Donations-focused snapshot routes for future module activation.
urlpatterns = [
    path('donate/', views.select_foodbank_for_donation, name='donate'),
    path('donate/to/<int:foodbank_id>/', views.donate_to_foodbank_general, name='donate_to_foodbank_general'),
    path('donate/<int:request_id>/', views.donate_to_foodbank, name='donate_to_foodbank'),
    path('donation/<int:donation_id>/allocate/', views.allocate_donation, name='allocate_donation'),
    path('donation/<int:donation_id>/allocations/', views.view_donation_allocations, name='view_donation_allocations'),
    path('donation/<int:donation_id>/accept/', views.accept_donation, name='accept_donation'),
    path('donation/<int:donation_id>/decline/', views.decline_donation, name='decline_donation'),
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('confirm-payment/', views.confirm_payment, name='confirm_payment'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancelled/', views.payment_cancelled, name='payment_cancelled'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
]
