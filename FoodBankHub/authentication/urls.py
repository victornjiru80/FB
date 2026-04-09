from django.urls import path
from . import views
from . import subscription_views
from . import donation_views
from . import donor_detailed_views
from . import donor_export_views
from . import views_allocation
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),
    path('csrf-debug/', views.csrf_debug, name='csrf_debug'),  # Debug endpoint
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/donor/', views.DonorRegistrationView.as_view(), name='register_donor'),
    path('register/foodbank/', views.FoodBankRegistrationView.as_view(), name='register_foodbank'),
    path('register/recipient/', views.RecipientRegistrationView.as_view(), name='register_recipient'),
    path('register/admin/', views.AdminRegistrationView.as_view(), name='register_admin'),
    path('registration/pending/', TemplateView.as_view(template_name='authentication/registration_pending.html'), name='registration_pending'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/request/create/', views.create_foodbank_request, name='create_foodbank_request'),
    path('dashboard/request/<int:pk>/edit/', views.edit_foodbank_request, name='edit_foodbank_request'),
    path('dashboard/request/<int:pk>/delete/', views.delete_foodbank_request, name='delete_foodbank_request'),
    path('dashboard/request/<int:pk>/fulfill/', views.fulfill_foodbank_request, name='fulfill_foodbank_request'),
    path('donor/settings/', views.donor_settings, name='donor_settings'),
    path('donate/', views.select_foodbank_for_donation, name='donate'),
    path('donate/to/<int:foodbank_id>/', views.donate_to_foodbank_general, name='donate_to_foodbank_general'),
    path('donate/<int:request_id>/', views.donate_to_foodbank, name='donate_to_foodbank'),
    path('units/add/', views.add_quantity_unit, name='add_quantity_unit'),
    path('foodbank-requests/', views.view_foodbank_requests, name='view_foodbank_requests'),
    #path('foodbank_linked_requests/', views.view_foodbank_linked_requests, name='view_foodbank_requests'),
    path('donation-history/', views.donation_history, name='donation_history'),
    path('notifications/acknowledgements/', views.notifications_acknowledgements, name='notifications_acknowledgements'),
    path('notifications/requests/', views.notifications_requests, name='notifications_requests'),
    path('notifications/system-updates/', views.notifications_system_updates, name='notifications_system_updates'),
    path('donor/change-password/', views.change_password, name='change_password'),
    path('donor/support/', views.contact_support, name='contact_support'),
    path('donor/privacy/', views.privacy_settings, name='privacy_settings'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='authentication/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='authentication/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='authentication/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='authentication/password_reset_complete.html'), name='password_reset_complete'),
    path('dashboard/donations/', views.foodbank_donations, name='foodbank_donations'),
    path('dashboard/analytics/', views.foodbank_donations, name='foodbank_analytics'),
    path('dashboard/settings/', views.foodbank_settings, name='foodbank_settings'),
    path('dashboard/settings/profile/', views.update_foodbank_profile, name='update_foodbank_profile'),
    path('dashboard/settings/password/', views.change_foodbank_password, name='change_foodbank_password'),
    path('dashboard/requests/', views.foodbank_requests, name='foodbank_requests'),
    path('dashboard/requests/export/<str:format>/', views.export_foodbank_requests_list, name='export_foodbank_requests'),
    path('notifications/foodbank/', views.notifications_foodbank, name='notifications_foodbank'),
    path('notifications/foodbank/system/', views.notifications_foodbank_system, name='notifications_foodbank_system'),
    path('notifications/foodbank/requests/', views.notifications_foodbank_requests, name='notifications_foodbank_requests'),
    path('notifications/mark-read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('donation/<int:donation_id>/allocate/', views.allocate_donation, name='allocate_donation'),
    path('donation/<int:donation_id>/allocations/', views.view_donation_allocations, name='view_donation_allocations'),
    path('analytics/', views.donation_analytics, name='donation_analytics'),
    path('recipient/request/create/', views.create_recipient_request, name='create_recipient_request'),
    path('recipient/request/select-foodbank/', views.select_foodbank_for_request, name='select_foodbank_for_request'),
    path('recipient/request/create/<int:foodbank_id>/', views.create_recipient_request_with_foodbank, name='create_recipient_request_with_foodbank'),
    path('recipient/requests/<int:pk>/', views.view_recipient_request_detail, name='view_recipient_request_detail'),
    path('recipient/requests/<int:pk>/edit/', views.edit_recipient_request, name='edit_recipient_request'),
    path('recipient/requests/<int:pk>/delete/', views.delete_recipient_request, name='delete_recipient_request'),
    # Recipient support and privacy
    path('recipient/contact-support/', views.recipient_contact_support, name='recipient_contact_support'),
    path('recipient/privacy-settings/', views.recipient_privacy_settings, name='recipient_privacy_settings'),
    # List recipient's own requests - REMOVED: Use recipient_requests_view instead

    # View available random donations
    path('recipient/random-donations/', views.available_random_donations, name='available_random_donations'),

    # Acknowledge a donation allocation
    path('recipient/acknowledge/<int:allocation_id>/', views.acknowledge_donation, name='acknowledge_donation'),
    # Recipient notifications

    path('recipient/notifications/', views.recipient_notifications, name='recipient_notifications'),

    # Testimonial management - Recipients
    path('recipient/testimonials/', views.recipient_testimonials_list, name='recipient_testimonials_list'),
    path('recipient/testimonial/add/', views.create_testimonial, name='create_testimonial'),
    path('recipient/testimonial/edit/<int:testimonial_id>/', views.edit_testimonial, name='edit_testimonial'),
    path('recipient/testimonial/delete/<int:testimonial_id>/', views.delete_testimonial, name='delete_testimonial'),
    path('recipient/testimonial/toggle/<int:testimonial_id>/', views.toggle_testimonial_display, name='toggle_testimonial_display'),
    
    # Testimonial management - Admin
    path('admin/testimonials/pending/', views.admin_testimonials_pending, name='admin_testimonials_pending'),
    path('admin/testimonials/all/', views.admin_all_testimonials, name='admin_all_testimonials'),
    path('admin/testimonial/approve/<int:testimonial_id>/', views.admin_approve_testimonial, name='admin_approve_testimonial'),
    path('admin/testimonial/reject/<int:testimonial_id>/', views.admin_reject_testimonial, name='admin_reject_testimonial'),

    path("recipient/random-donations/accept/<int:donation_id>/", views.accept_random_donation, name="accept_random_donation"),
    
    # Discussion system for 'other' type donations (Donor ↔ Foodbank)
    path('foodbank/other-donations/', views.available_other_donations, name='available_other_donations'),
    path('foodbank/discussion/start/<int:donation_id>/', views.start_donation_discussion, name='start_donation_discussion'),
    path('discussion/<int:discussion_id>/', views.donation_discussion_detail, name='donation_discussion_detail'),
    path('my-discussions/', views.my_donation_discussions, name='my_donation_discussions'),
    path('foodbank/accepted-csr-donations/', views.accepted_csr_donations, name='accepted_csr_donations'),
    
    # M-Pesa callback
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    
    #dismiss notifications
    path('recipient/notifications/<int:pk>/dismiss/', views.dismiss_notification, name='dismiss_notification'),
    path('request/<int:request_id>/acknowledge/', views.acknowledge_request, name='acknowledge_request'),
    path('request/<int:request_id>/confirm-received/', views.confirm_request_received, name='confirm_request_received'),
    path('request/<int:request_id>/recipient-decline/', views.recipient_decline_request, name='recipient_decline_request'),


    #path("available-foodbanks/", views.available_foodbanks, name="available_foodbanks"),

    
    
    # Food Bank Public Profile URLs
    path('foodbank/<int:foodbank_id>/', views.foodbank_public_profile, name='foodbank_public_profile'),
    path('dashboard/manage-profile/', views.manage_foodbank_profile, name='manage_foodbank_profile'),
    
    # Payment URLs
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('confirm-payment/', views.confirm_payment, name='confirm_payment'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancelled/', views.payment_cancelled, name='payment_cancelled'),
    
    # Recipient Settings URLs
    path('recipient/settings/', views.recipient_settings, name='recipient_settings'),
    path('recipient/change-password/', views.change_recipient_password, name='change_recipient_password'),
    path('recipient/foodbanks/', views.recipient_foodbanks_list, name='recipient_foodbanks_list'),
    path("donations/acknowledge/", views.all_donations_to_acknowledge, name="all_donations_to_acknowledge"),
    # urls.py
    path('request/<int:pk>/accept/', views.accept_request, name='accept_request'),
    #path('request/<int:pk>/decline/', views.decline_request, name='decline_request'),
    path('recipient/download-data/', views.download_recipient_data, name='download_recipient_data'),
    #path('request/<int:pk>/fulfill/', views.fulfill_request, name='fulfill_request'),
    #api for location - removed
    #api for ussd 
    path("ussd/", views.ussd_callback, name="ussd_callback"),
    
    # Support payment
    path('support-payment/', views.support_payment, name='support_payment'),
    path('my-support-donations/', views.my_support_donations, name='my_support_donations'),
    path('my-support-donations/export/excel/', views.export_my_support_donations_excel, name='export_my_support_donations_excel'),
    path('my-support-donations/export/pdf/', views.export_my_support_donations_pdf, name='export_my_support_donations_pdf'),
    
    # Admin foodbank approval URLs
    path('admin/pending-registrations/', views.admin_pending_registrations, name='admin_pending_registrations'),
    path('admin/approve-foodbank/<int:foodbank_id>/', views.approve_foodbank_registration, name='approve_foodbank_registration'),
    path('admin/reject-foodbank/<int:foodbank_id>/', views.reject_foodbank_registration, name='reject_foodbank_registration'),
    path('admin/view-application/<int:foodbank_id>/', views.view_foodbank_application, name='view_foodbank_application'),
    
    # Foodbank - Recipient Request Management
    # Removed: view_approved_requests - redundant with dashboard filters
    path('foodbank/request/<int:pk>/fulfill/', views.fulfill_recipient_request, name='fulfill_recipient_request'),
    path('foodbank/request/<int:pk>/complete/', views.mark_request_completed, name='mark_request_completed'),


    # Contact support pages
    path('donor/contact-support/', views.donor_contact_support, name='donor_contact_support'),
    path('foodbank/contact-support/', views.foodbank_contact_support, name='foodbank_contact_support'),
    path('requests/in-progress/', views.view_in_progress_requests, name='view_in_progress_requests'),
    path('foodbank/request/<int:recipient_request_id>/mark-received/', views.mark_received, name='mark_received'),
    
    # Support messages viewing for all users
    path('my-support-messages/', views.my_support_messages, name='my_support_messages'),
    path('my-support-messages/<int:message_id>/', views.support_message_detail_user, name='support_message_detail_user'),
    
    # Foodbank Testimonial URLs
    path('foodbank/testimonials/create/', views.create_foodbank_testimonial, name='create_foodbank_testimonial'),
    path('foodbank/testimonials/', views.foodbank_testimonials_list, name='foodbank_testimonials_list'),
    path('foodbank/testimonials/<int:testimonial_id>/edit/', views.edit_foodbank_testimonial, name='edit_foodbank_testimonial'),
    path('foodbank/testimonials/<int:testimonial_id>/delete/', views.delete_foodbank_testimonial, name='delete_foodbank_testimonial'),
    path('foodbank/testimonials/<int:testimonial_id>/toggle-display/', views.toggle_foodbank_testimonial_display, name='toggle_foodbank_testimonial_display'),
    
    # Admin Foodbank Testimonial Management URLs
    path('admin/foodbank-testimonials/pending/', views.admin_foodbank_testimonials_pending, name='admin_foodbank_testimonials_pending'),
    path('admin/foodbank-testimonial/approve/<int:testimonial_id>/', views.admin_approve_foodbank_testimonial, name='admin_approve_foodbank_testimonial'),
    path('admin/foodbank-testimonial/reject/<int:testimonial_id>/', views.admin_reject_foodbank_testimonial, name='admin_reject_foodbank_testimonial'),
    path('admin/foodbank-testimonials/all/', views.admin_all_foodbank_testimonials, name='admin_all_foodbank_testimonials'),

    # Donor Testimonial URLs
    path('donor/testimonials/create/', views.create_donor_testimonial, name='create_donor_testimonial'),
    path('donor/testimonials/', views.donor_testimonials_list, name='donor_testimonials_list'),
    path('donor/testimonials/<int:testimonial_id>/edit/', views.edit_donor_testimonial, name='edit_donor_testimonial'),
    path('donor/testimonials/<int:testimonial_id>/delete/', views.delete_donor_testimonial, name='delete_donor_testimonial'),
    path('donor/testimonials/<int:testimonial_id>/toggle-display/', views.toggle_donor_testimonial_display, name='toggle_donor_testimonial_display'),
    
    # Admin Donor Testimonial Management URLs
    path('admin/donor-testimonials/pending/', views.admin_donor_testimonials_pending, name='admin_donor_testimonials_pending'),
    path('admin/donor-testimonial/approve/<int:testimonial_id>/', views.admin_approve_donor_testimonial, name='admin_approve_donor_testimonial'),
    path('admin/donor-testimonial/reject/<int:testimonial_id>/', views.admin_reject_donor_testimonial, name='admin_reject_donor_testimonial'),
    path('admin/donor-testimonials/all/', views.admin_all_donor_testimonials, name='admin_all_donor_testimonials'),

    # ==================== REQUEST MANAGEMENT URLS ====================
    # Recipient request management
    path('recipient/my-requests/', views.recipient_requests_view, name='recipient_requests_view'),
    path('recipient/my-requests/export/<str:format>/', views.export_recipient_requests, name='export_recipient_requests'),
    path('recipient/create-request/', views.create_request, name='create_request'),
    
    # Foodbank request management
    path('foodbank/manage-requests/', views.foodbank_requests_view, name='foodbank_requests_view'),
    path('foodbank/manage-requests/export/<str:format>/', views.export_foodbank_requests, name='export_foodbank_manage_requests'),
    path('foodbank/inventory/', views.foodbank_inventory, name='foodbank_inventory'),
    path('foodbank/inventory/export/', views.export_foodbank_inventory, name='export_foodbank_inventory'),
    path('foodbank/allocate-donation/', views_allocation.allocate_donation, name='allocate_donation'),
    path('api/search-recipients/', views_allocation.search_recipients, name='search_recipients'),
    path('recipient/acknowledge-allocation/<int:allocation_id>/', views_allocation.acknowledge_allocation, name='acknowledge_allocation'),
    path('api/request/<int:request_id>/update-status/', views.update_request_status, name='update_request_status'),
    
    # Shared request detail view
    path('request/<int:request_id>/detail/', views.request_detail, name='request_detail'),
    path('subscription/manage/', views.manage_subscription, name='manage_subscription'),
    
    # Subscription URLs for Food Banks
    path('subscription/status/', subscription_views.subscription_status, name='subscription_status'),
    path('subscription/requests/', subscription_views.subscription_requests, name='subscription_requests'),
    path('subscription/status/export/excel/', subscription_views.export_subscription_payments_excel, name='subscription_payments_export_excel'),
    path('subscription/status/export/pdf/', subscription_views.export_subscription_payments_pdf, name='subscription_payments_export_pdf'),
    path('subscription/subscribe/', subscription_views.subscribe, name='subscribe'),
    path('subscription/payment/<int:payment_id>/', subscription_views.payment_detail, name='payment_detail_foodbank'),
    path('subscription/info/', subscription_views.subscription_info, name='subscription_info'),
    
    # Donation Management URLs
    path('donations/donor/', donation_views.donor_donations_list, name='donor_donations_list'),
    path('donations/donor/export/<str:format>/', donation_views.donor_donations_export, name='donor_donations_export'),
    
    # Donor Detailed Donation Views
    path('donations/donor/unspecified/', donor_detailed_views.donor_unspecified_donations_detail, name='donor_unspecified_donations_detail'),
    path('donations/donor/unspecified/export/<str:format>/', donor_export_views.donor_unspecified_export, name='donor_unspecified_export'),
    path('donations/donor/subsidized/', donor_detailed_views.donor_subsidized_donations_detail, name='donor_subsidized_donations_detail'),
    path('donations/donor/subsidized/export/<str:format>/', donor_export_views.donor_subsidized_export, name='donor_subsidized_export'),
    path('donations/donor/request-based/', donor_detailed_views.donor_request_donations_detail, name='donor_request_donations_detail'),
    path('donations/foodbank/', donation_views.foodbank_donations_list, name='foodbank_donations_list'),
    path('donations/foodbank/', donation_views.foodbank_donations_list, name='foodbank_donations_card'),
    path('donations/foodbank/export/', donation_views.foodbank_donations_export, name='foodbank_donations_export'),
    path('donations/<int:donation_id>/', donation_views.donation_detail, name='donation_detail'),
    path('donation/<int:donation_id>/accept/', views.accept_donation, name='accept_donation'),
    path('donation/<int:donation_id>/decline/', views.decline_donation, name='decline_donation'),
    path('request/<int:request_id>/fulfill/', views.fulfill_request, name='fulfill_request'),
    path('request/<int:request_id>/partial-fulfill/', views.partial_fulfill_request, name='partial_fulfill_request'),
    path('request/<int:request_id>/fulfill-rest/', views.fulfill_request_rest, name='fulfill_request_rest'),
    path('request/<int:request_id>/decline/', views.decline_request, name='decline_request'),
    
    # Recipient Data Export
    path('recipient/download-requests-excel/', views.download_recipient_requests_excel, name='download_recipient_requests_excel'),
    path('request/<int:request_id>/assign/', views.assign_anonymous_request, name='assign_anonymous_request'),
    path('donation/<int:donation_id>/allocate-to-request/', views.allocate_donation_to_request, name='allocate_from_donation'),
    path('account/delete/', views.request_account_deletion, name='request_account_deletion'),
    path('donations/subsidized/', views.recipient_subsidized_donations, name='recipient_subsidized_donations'),
    path('donations/subsidized/export/<str:format>/', views.export_subsidized_donations, name='export_subsidized_donations'),
    path('donation/<int:donation_id>/respond/', views.respond_to_subsidized, name='respond_to_subsidized'),
    path('donation/<int:donation_id>/confirm-received/', views.confirm_subsidized_received, name='confirm_subsidized_received'),
    path('subsidized-responses/', views.foodbank_subsidized_responses, name='foodbank_subsidized_responses'),
    
    # ==================== UNSPECIFIED DONATION MANAGEMENT ====================
    # Foodbank management of unspecified donations
    path('foodbank/unspecified-donations/', views.foodbank_unspecified_donations, name='foodbank_unspecified_donations'),
    path('foodbank/unspecified-donations/export/', views.foodbank_export_unspecified_donations, name='foodbank_export_unspecified_donations'),
    path('foodbank/unspecified-donation/<int:donation_id>/accept/', views.foodbank_accept_unspecified_donation, name='foodbank_accept_unspecified_donation'),
    path('foodbank/unspecified-donation/<int:donation_id>/decline/', views.foodbank_decline_unspecified_donation, name='foodbank_decline_unspecified_donation'),
    
    # Subsidized Donations Management
    path('foodbank/subsidized-donations/', views.foodbank_subsidized_donations, name='foodbank_subsidized_donations'),
    path('foodbank/subsidized-donations/export/', views.foodbank_subsidized_donations_export, name='foodbank_subsidized_donations_export'),
    path('foodbank/subsidized-donation/<int:donation_id>/accept/', views.foodbank_accept_subsidized_donation, name='foodbank_accept_subsidized_donation'),
    path('foodbank/subsidized-donation/<int:donation_id>/decline/', views.foodbank_decline_subsidized_donation, name='foodbank_decline_subsidized_donation'),
    
    # Recipient management of available donations (org recipients only)
    path('recipient/available-donations/', views.recipient_available_donations, name='recipient_available_donations'),
    path('recipient/available-donations/export/<str:format>/', views.export_available_donations, name='export_available_donations'),
    path('recipient/unspecified-donation/<int:donation_id>/accept/', views.recipient_accept_unspecified_donation, name='recipient_accept_unspecified_donation'),
    path('recipient/unspecified-donation/<int:donation_id>/decline/', views.recipient_decline_unspecified_donation, name='recipient_decline_unspecified_donation'),
    path('recipient/unspecified-donation/<int:donation_id>/confirm-received/', views.recipient_confirm_unspecified_received, name='recipient_confirm_unspecified_received'),
    
    # Recipient subsidized donation actions
    path('recipient/subsidized-donation/<int:donation_id>/accept/', views.recipient_accept_subsidized_donation, name='recipient_accept_subsidized_donation'),
    path('recipient/subsidized-donation/<int:donation_id>/confirm-received/', views.recipient_confirm_subsidized_donation_received, name='recipient_confirm_subsidized_received'),
    path('submit-remaining/<int:request_id>/', views.submit_remaining_to_donors, name='submit_remaining_to_donors'),
    
    # Request Donation Management (Foodbank Accept/Reject)
    path('foodbank/request-donation/<int:donation_id>/accept/', views.accept_request_donation, name='accept_request_donation'),
    path('foodbank/request-donation/<int:donation_id>/reject/', views.reject_request_donation, name='reject_request_donation'),
]
