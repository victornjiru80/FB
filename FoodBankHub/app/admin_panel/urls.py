from django.urls import path
from . import views
from . import views_donations
from . import views_account_deletion
from . import views_impact
from . import views_posted_donations
from . import environmental_exports
from . import user_actions

app_name = 'custom_admin'

urlpatterns = [
    # Authentication
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    
    # Dashboard
    path('', views.dashboard_home, name='dashboard'),
    
    # Analytics & Impact
    path('impact/environmental/', views_impact.environmental_impact_dashboard, name='environmental_impact'),
    path('impact/environmental-reports/', views_impact.environmental_impact_reports, name='environmental_impact_reports'),
    path('impact/environmental-reports/received/', views_impact.received_donations_impact_list, name='received_donations_impact_list'),
    path('impact/environmental-reports/donations/', views_impact.impact_donations_list, name='impact_donations_list'),
    path('impact/environmental-reports/donations/export-pdf/', views_impact.export_impact_donations_pdf, name='export_impact_donations_pdf'),
    path('impact/environmental-reports/donations/export-excel/', views_impact.export_impact_donations_excel, name='export_impact_donations_excel'),
    path('impact/environmental-reports/monthly/', views_impact.impact_monthly_breakdown, name='impact_monthly_breakdown'),
    path('impact/environmental-reports/monthly/export-pdf/', views_impact.export_impact_monthly_pdf, name='export_impact_monthly_pdf'),
    path('impact/environmental-reports/monthly/export-excel/', views_impact.export_impact_monthly_excel, name='export_impact_monthly_excel'),
    path('impact/environmental-reports/donors/', views_impact.impact_donors_list, name='impact_donors_list'),
    path('impact/environmental-reports/donors/export-pdf/', views_impact.export_impact_donors_pdf, name='export_impact_donors_pdf'),
    path('impact/environmental-reports/donors/export-excel/', views_impact.export_impact_donors_excel, name='export_impact_donors_excel'),
    path('impact/environmental-reports/foodbanks/', views_impact.impact_foodbanks_list, name='impact_foodbanks_list'),
    path('impact/environmental-reports/foodbanks/export-pdf/', views_impact.export_impact_foodbanks_pdf, name='export_impact_foodbanks_pdf'),
    path('impact/environmental-reports/foodbanks/export-excel/', views_impact.export_impact_foodbanks_excel, name='export_impact_foodbanks_excel'),
    path('impact/export-pdf/', views_impact.export_impact_report_pdf, name='export_impact_report_pdf'),
    path('impact/environmental-reports/export-pdf/', environmental_exports.export_environmental_reports_pdf, name='export_environmental_reports_pdf'),
    path('impact/environmental/posted/unspecified/export-excel/', views_impact.export_environmental_posted_unspecified_excel, name='export_environmental_posted_unspecified_excel'),
    path('impact/environmental/posted/unspecified/export-pdf/', views_impact.export_environmental_posted_unspecified_pdf, name='export_environmental_posted_unspecified_pdf'),
    path('impact/environmental/posted/subsidized/export-excel/', views_impact.export_environmental_posted_subsidized_excel, name='export_environmental_posted_subsidized_excel'),
    path('impact/environmental/posted/subsidized/export-pdf/', views_impact.export_environmental_posted_subsidized_pdf, name='export_environmental_posted_subsidized_pdf'),
    path('impact/environmental/posted/specified/export-excel/', views_impact.export_environmental_posted_specified_excel, name='export_environmental_posted_specified_excel'),
    path('impact/environmental/posted/specified/export-pdf/', views_impact.export_environmental_posted_specified_pdf, name='export_environmental_posted_specified_pdf'),
    
    # User Management
    path('users/', views.user_management, name='user_management'),
    path('users/donors/', views.donors_management, name='donors_management'),
    path('users/foodbanks/', views.foodbanks_management, name='foodbanks_management'),
    path('users/recipients/', views.recipients_management, name='recipients_management'),
    path('users/admins/', views.admins_management, name='admins_management'),
    path('users/admins/export-pdf/', views.export_admins_pdf, name='export_admins_pdf'),
    path('users/admins/export-excel/', views.export_admins_excel, name='export_admins_excel'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-status/', user_actions.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/delete/', user_actions.delete_user, name='delete_user'),
    
    # Donation Management - Legacy
    path('donations/', views.donation_management, name='donation_management'),
    
    # Comprehensive Donations Management
    path('donations/overview/', views_donations.donations_overview_dashboard, name='donations_overview'),
    path('donations/recipient-requests/', views_donations.recipient_requests_management, name='recipient_requests_management'),
    path('donations/foodbank-requests/', views_donations.foodbank_requests_enhanced, name='foodbank_requests_enhanced'),
    path('donations/donor-donations/', views_donations.donor_donations_management, name='donor_donations_management'),
    path('donations/received/', views_donations.received_donations_management, name='received_donations_management'),
    path('donations/received/export-csv/', views_donations.export_received_donations_csv, name='export_received_donations_csv'),
    path('donations/received/export-pdf/', views_donations.export_received_donations_pdf, name='export_received_donations_pdf'),
    path('donations/allocations/', views_donations.donation_allocations_management, name='donation_allocations_management'),
    path('donations/discussions/', views_donations.donation_discussions_management, name='donation_discussions_management'),
    path('donations/transactions/', views_donations.payment_transactions_management, name='payment_transactions_management'),
    path('donations/unspecified/', views_donations.unspecified_donations_management, name='unspecified_donations_management'),
    path('donations/unspecified/export-csv/', views_donations.export_unspecified_donations_csv, name='export_unspecified_donations_csv'),
    path('donations/unspecified/export-excel/', views_donations.export_unspecified_donations_excel, name='export_unspecified_donations_excel'),
    path('donations/unspecified/export-pdf/', views_donations.export_unspecified_donations_pdf, name='export_unspecified_donations_pdf'),
    path('donations/unspecified/<int:donation_id>/details/', views_donations.unspecified_donation_details, name='unspecified_donation_details'),
    path('donations/unspecified/<int:donation_id>/export-pdf/', views_donations.export_donation_details_pdf, name='export_donation_details_pdf'),
    path('donations/subsidized/', views_donations.subsidized_donations_management, name='subsidized_donations_management'),
    path('donations/subsidized/export-csv/', views_donations.export_subsidized_donations_csv, name='export_subsidized_donations_csv'),
    path('donations/subsidized/export-excel/', views_donations.export_subsidized_donations_excel, name='export_subsidized_donations_excel'),
    path('donations/subsidized/export-pdf/', views_donations.export_subsidized_donations_pdf, name='export_subsidized_donations_pdf'),
    path('donations/subsidized/<int:donation_id>/details/', views_donations.subsidized_donation_details, name='subsidized_donation_details'),
    path('donations/subsidized/<int:donation_id>/export-pdf/', views_donations.export_subsidized_donation_details_pdf, name='export_subsidized_donation_details_pdf'),
    path('donations/direct/', views_donations.direct_donations_management, name='direct_donations_management'),
    path('donations/direct/manage/', views_donations.direct_donations_manage, name='direct_donations_manage'),
    path('donations/specified/', views_donations.specified_donations_management, name='specified_donations_management'),
    path('donations/specified/export-csv/', views_donations.export_specified_donations_csv, name='export_specified_donations_csv'),
    path('donations/specified/export-excel/', views_donations.export_specified_donations_excel, name='export_specified_donations_excel'),
    path('donations/specified/export-pdf/', views_donations.export_specified_donations_pdf, name='export_specified_donations_pdf'),
    path('donations/direct/inventory/', views_donations.direct_donations_inventory, name='direct_donations_inventory'),
    path('donations/direct/export-excel/', views_donations.export_direct_donations_excel, name='export_direct_donations_excel'),
    path('donations/direct/export-pdf/', views_donations.export_direct_donations_pdf, name='export_direct_donations_pdf'),
    path('donations/direct/<int:donation_id>/details/', views_donations.direct_donation_details, name='direct_donation_details'),
    path('donations/direct/<int:donation_id>/export-pdf/', views_donations.export_direct_donation_details_pdf, name='export_direct_donation_details_pdf'),
    path('donations/request-management/', views_donations.request_management_admin, name='request_management_admin'),
    path('donations/responses/', views_donations.donation_responses_management, name='donation_responses_management'),
    path('donations/posted/', views_posted_donations.posted_donations_management, name='posted_donations_management'),
    path('donations/posted/unspecified/', views_posted_donations.posted_unspecified_donations, name='posted_unspecified_donations'),
    path('donations/posted/subsidized/', views_posted_donations.posted_subsidized_donations, name='posted_subsidized_donations'),
    path('donations/posted/specified/', views_posted_donations.posted_specified_donations, name='posted_specified_donations'),
    path('donations/posted/<int:donation_id>/', views_posted_donations.posted_donation_detail, name='posted_donation_detail'),
    

    # Food Bank Requests - Legacy
    path('requests/', views.foodbank_requests, name='foodbank_requests'),
    
    # Food Bank Approvals
    path('approvals/', views.foodbank_approvals, name='foodbank_approvals'),
    path('approvals/export-excel/', views.export_foodbank_approvals_excel, name='export_foodbank_approvals_excel'),
    path('approvals/export-pdf/', views.export_foodbank_approvals_pdf, name='export_foodbank_approvals_pdf'),
    path('approvals/export-csv/', views.export_foodbank_approvals_csv, name='export_foodbank_approvals_csv'),
    path('approvals/approved/', views.approved_foodbanks, name='approved_foodbanks'),
    path('approvals/approved/export-excel/', views.export_approved_foodbanks_excel, name='export_approved_foodbanks_excel'),
    path('approvals/approved/export-pdf/', views.export_approved_foodbanks_pdf, name='export_approved_foodbanks_pdf'),
    path('approvals/approved/export-csv/', views.export_approved_foodbanks_csv, name='export_approved_foodbanks_csv'),
    path('approvals/rejected/', views.rejected_foodbank_applications, name='rejected_foodbank_applications'),
    path('approvals/rejected/export-excel/', views.export_rejected_foodbank_applications_excel, name='export_rejected_foodbank_applications_excel'),
    path('approvals/rejected/export-pdf/', views.export_rejected_foodbank_applications_pdf, name='export_rejected_foodbank_applications_pdf'),
    path('approvals/rejected/export-csv/', views.export_rejected_foodbank_applications_csv, name='export_rejected_foodbank_applications_csv'),
    path('approvals/<int:foodbank_id>/approve/', views.approve_foodbank, name='approve_foodbank'),
    path('approvals/<int:foodbank_id>/reject/', views.reject_foodbank, name='reject_foodbank'),
    path('approvals/<int:foodbank_id>/reopen/', views.reopen_foodbank_application, name='reopen_foodbank_application'),
    path('approvals/<int:foodbank_id>/reopen-approved/', views.reopen_approved_foodbank, name='reopen_approved_foodbank'),
    path('approvals/<int:foodbank_id>/view/', views.view_foodbank_application, name='view_foodbank_application'),
    
    # Bulk Actions
    path('bulk-actions/', views.bulk_actions, name='bulk_actions'),
    
    # Reports
    path('analytics/', views.analytics, name='analytics'),
    path('export/<str:report_type>/', views.export_report, name='export_report'),
    
    # Comprehensive Reports
    path('reports/recipient-requests/', views.recipient_requests_report, name='recipient_requests_report'),
    path('reports/foodbank-requests/', views.foodbank_requests_report, name='foodbank_requests_report'),
    path('reports/donor-donations/', views.donor_donations_report, name='donor_donations_report'),
    path('reports/complete-donation-flow/', views.complete_donation_flow_report, name='complete_donation_flow_report'),
    
    # Support Messages
    path('support-messages/', views.support_messages, name='support_messages'),
    path('support-messages/<int:message_id>/', views.support_message_detail, name='support_message_detail'),

    # Testimonials
    path('testimonials/', views.testimonials_overview, name='testimonials_overview'),
    path('testimonials/<str:category>/', views.testimonials_category, name='testimonials_category'),
    path('testimonials/<str:category>/<str:status>/', views.testimonials_category_status, name='testimonials_category_status'),
    path('testimonials/<str:category>/<int:testimonial_id>/approve/', views.approve_testimonial, name='approve_testimonial'),
    path('testimonials/<str:category>/<int:testimonial_id>/reject/', views.reject_testimonial, name='reject_testimonial'),
    path('testimonials/<str:category>/<int:testimonial_id>/hide/', views.hide_testimonial, name='hide_testimonial'),
    path('testimonials/<str:category>/<int:testimonial_id>/restore/', views.restore_testimonial, name='restore_testimonial'),
    path('testimonials/<str:category>/<int:testimonial_id>/pdf/', views.download_testimonial_pdf, name='download_testimonial_pdf'),
    
    # Subscription Management
    path('subscriptions/', views.subscription_management, name='subscription_management'),
    path('subscriptions/<int:subscription_id>/', views.subscription_detail, name='subscription_detail'),
    path('subscriptions/export-excel/', views.export_subscriptions_excel, name='export_subscriptions_excel'),
    path('subscriptions/export-pdf/', views.export_subscriptions_pdf, name='export_subscriptions_pdf'),
    path('subscriptions/export-csv/', views.export_subscriptions_csv, name='export_subscriptions_csv'),
    path('subscriptions/expired/', views.expired_accounts, name='expired_accounts'),
    path('subscriptions/posted/', views.posted_subscriptions, name='posted_subscriptions'),
    path('subscriptions/posted/export-excel/', views.export_posted_subscriptions_excel, name='export_posted_subscriptions_excel'),
    path('subscriptions/posted/export-pdf/', views.export_posted_subscriptions_pdf, name='export_posted_subscriptions_pdf'),
    path('subscriptions/posted/export-csv/', views.export_posted_subscriptions_csv, name='export_posted_subscriptions_csv'),
    path('payments/', views.payment_verification, name='payment_verification'),
    path('payments/export-excel/', views.export_payment_verification_excel, name='export_payment_verification_excel'),
    path('payments/export-pdf/', views.export_payment_verification_pdf, name='export_payment_verification_pdf'),
    path('payments/export-csv/', views.export_payment_verification_csv, name='export_payment_verification_csv'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    
    # Login Logs
    path('login-logs/', views.admin_login_logs, name='admin_login_logs'),
    
    # Admin Codes Management (Superuser only)
    path('admin-codes/', views.admin_codes_management, name='admin_codes_management'),
    path('admin-codes/export-excel/', views.export_admin_codes_excel, name='export_admin_codes_excel'),
    path('admin-codes/export-pdf/', views.export_admin_codes_pdf, name='export_admin_codes_pdf'),
    
    # System Support Donations
    path('system-support-donations/', views.system_support_donations, name='system_support_donations'),
    path('system-support-donations/export-excel/', views.export_system_support_donations_excel, name='export_system_support_donations_excel'),
    path('system-support-donations/export-pdf/', views.export_system_support_donations_pdf, name='export_system_support_donations_pdf'),
    path('system-support-donations/<int:donation_id>/', views.system_support_donation_detail, name='system_support_donation_detail'),
    
    # Account Deletion Requests
    path('account-deletions/', views_account_deletion.account_deletion_requests, name='account_deletion_requests'),
    path('account-deletions/<int:request_id>/', views_account_deletion.account_deletion_detail, name='account_deletion_detail'),
    path('account-deletions/<int:request_id>/approve/', views_account_deletion.approve_deletion_request, name='approve_deletion_request'),
    path('account-deletions/<int:request_id>/reject/', views_account_deletion.reject_deletion_request, name='reject_deletion_request'),
    path('account-deletions/bulk-process/', views_account_deletion.bulk_process_deletion_requests, name='bulk_process_deletion_requests'),
    path('account-deletions/stats/', views_account_deletion.deletion_requests_stats, name='deletion_requests_stats'),
    
    # News Section Management
    path('news-sections/', views.news_section_list, name='news_section_list'),
    path('news-sections/create/', views.news_section_create, name='news_section_create'),
    path('news-sections/<int:news_id>/edit/', views.news_section_edit, name='news_section_edit'),
    path('news-sections/<int:news_id>/delete/', views.news_section_delete, name='news_section_delete'),
    path('news-sections/<int:news_id>/toggle/', views.news_section_toggle, name='news_section_toggle'),
    
    # Quick Actions
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    # API endpoints
    path('api/analytics/', views.analytics_api, name='analytics_api'),
]
