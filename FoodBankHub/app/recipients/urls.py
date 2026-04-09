from django.urls import path
from . import views

# Recipient-focused snapshot routes for future module activation.
urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recipient/settings/', views.recipient_settings, name='recipient_settings'),
    path('recipient/change-password/', views.change_recipient_password, name='change_recipient_password'),
    path('recipient/contact-support/', views.recipient_contact_support, name='recipient_contact_support'),
    path('recipient/privacy-settings/', views.recipient_privacy_settings, name='recipient_privacy_settings'),
    path('recipient/foodbanks/', views.recipient_foodbanks_list, name='recipient_foodbanks_list'),
    path('recipient/notifications/', views.recipient_notifications, name='recipient_notifications'),
    path('recipient/notifications/<int:pk>/dismiss/', views.dismiss_notification, name='dismiss_notification'),
    path('recipient/random-donations/', views.available_random_donations, name='available_random_donations'),
    path('recipient/random-donations/accept/<int:donation_id>/', views.accept_random_donation, name='accept_random_donation'),
    path('recipient/available-donations/', views.recipient_available_donations, name='recipient_available_donations'),
    path('recipient/my-requests/', views.recipient_requests_view, name='recipient_requests_view'),
    path('recipient/create-request/', views.create_request, name='create_request'),
    path('recipient/request/create/', views.create_recipient_request, name='create_recipient_request'),
    path('recipient/request/select-foodbank/', views.select_foodbank_for_request, name='select_foodbank_for_request'),
    path('recipient/testimonials/', views.recipient_testimonials_list, name='recipient_testimonials_list'),
    path('recipient/testimonial/add/', views.create_testimonial, name='create_testimonial'),
    path('recipient/testimonial/delete/<int:testimonial_id>/', views.delete_testimonial, name='delete_testimonial'),
]
