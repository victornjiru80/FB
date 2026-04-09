from django.urls import path
from . import views
from . import donor_detailed_views
from . import donor_export_views

# Donor-focused snapshot routes for future module activation.
urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('donor/settings/', views.donor_settings, name='donor_settings'),
    path('donor/change-password/', views.change_password, name='change_password'),
    path('donor/contact-support/', views.donor_contact_support, name='donor_contact_support'),
    path('donate/', views.select_foodbank_for_donation, name='donate'),
    path('donate/to/<int:foodbank_id>/', views.donate_to_foodbank_general, name='donate_to_foodbank_general'),
    path('donation-history/', views.donation_history, name='donation_history'),
    path('my-discussions/', views.my_donation_discussions, name='my_donation_discussions'),
    path('support-payment/', views.support_payment, name='support_payment'),
    path('my-support-donations/', views.my_support_donations, name='my_support_donations'),
    path('account/delete/', views.request_account_deletion, name='request_account_deletion'),
    path('notifications/acknowledgements/', views.notifications_acknowledgements, name='notifications_acknowledgements'),
    path('notifications/requests/', views.notifications_requests, name='notifications_requests'),
    path('notifications/system-updates/', views.notifications_system_updates, name='notifications_system_updates'),
    path('donor/testimonials/', views.donor_testimonials_list, name='donor_testimonials_list'),
    path('donor/testimonials/create/', views.create_donor_testimonial, name='create_donor_testimonial'),
    path('donor/testimonials/<int:testimonial_id>/edit/', views.edit_donor_testimonial, name='edit_donor_testimonial'),
    path('donor/testimonials/<int:testimonial_id>/delete/', views.delete_donor_testimonial, name='delete_donor_testimonial'),
    path('donor/testimonials/<int:testimonial_id>/toggle-display/', views.toggle_donor_testimonial_display, name='toggle_donor_testimonial_display'),
    path('donations/donor/unspecified/', donor_detailed_views.donor_unspecified_donations_detail, name='donor_unspecified_donations_detail'),
    path('donations/donor/unspecified/export/<str:format>/', donor_export_views.donor_unspecified_export, name='donor_unspecified_export'),
    path('donations/donor/subsidized/', donor_detailed_views.donor_subsidized_donations_detail, name='donor_subsidized_donations_detail'),
    path('donations/donor/subsidized/export/<str:format>/', donor_export_views.donor_subsidized_export, name='donor_subsidized_export'),
    path('donations/donor/request-based/', donor_detailed_views.donor_request_donations_detail, name='donor_request_donations_detail'),
]
