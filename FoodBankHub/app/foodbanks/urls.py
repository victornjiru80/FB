from django.urls import path
from . import views

# FoodBank-focused snapshot routes for future module activation.
urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/donations/', views.foodbank_donations, name='foodbank_donations'),
    path('dashboard/analytics/', views.foodbank_donations, name='foodbank_analytics'),
    path('dashboard/settings/', views.foodbank_settings, name='foodbank_settings'),
    path('dashboard/settings/profile/', views.update_foodbank_profile, name='update_foodbank_profile'),
    path('dashboard/settings/password/', views.change_foodbank_password, name='change_foodbank_password'),
    path('dashboard/manage-profile/', views.manage_foodbank_profile, name='manage_foodbank_profile'),
    path('dashboard/requests/', views.foodbank_requests, name='foodbank_requests'),
    path('dashboard/requests/export/<str:format>/', views.export_foodbank_requests_list, name='export_foodbank_requests'),
    path('foodbank/<int:foodbank_id>/', views.foodbank_public_profile, name='foodbank_public_profile'),
    path('foodbank/inventory/', views.foodbank_inventory, name='foodbank_inventory'),
    path('foodbank/inventory/export/', views.export_foodbank_inventory, name='export_foodbank_inventory'),
    path('foodbank/manage-requests/', views.foodbank_requests_view, name='foodbank_requests_view'),
    path('foodbank/manage-requests/export/<str:format>/', views.export_foodbank_requests, name='export_foodbank_manage_requests'),
    path('foodbank/contact-support/', views.foodbank_contact_support, name='foodbank_contact_support'),
    path('foodbank/other-donations/', views.available_other_donations, name='available_other_donations'),
    path('foodbank/discussion/start/<int:donation_id>/', views.start_donation_discussion, name='start_donation_discussion'),
    path('foodbank/accepted-csr-donations/', views.accepted_csr_donations, name='accepted_csr_donations'),
    path('foodbank/unspecified-donations/', views.foodbank_unspecified_donations, name='foodbank_unspecified_donations'),
    path('foodbank/subsidized-donations/', views.foodbank_subsidized_donations, name='foodbank_subsidized_donations'),
    path('notifications/foodbank/', views.notifications_foodbank, name='notifications_foodbank'),
    path('notifications/foodbank/system/', views.notifications_foodbank_system, name='notifications_foodbank_system'),
    path('notifications/foodbank/requests/', views.notifications_foodbank_requests, name='notifications_foodbank_requests'),
    path('foodbank/testimonials/', views.foodbank_testimonials_list, name='foodbank_testimonials_list'),
    path('foodbank/testimonials/create/', views.create_foodbank_testimonial, name='create_foodbank_testimonial'),
]
