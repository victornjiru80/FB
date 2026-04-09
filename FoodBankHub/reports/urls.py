from django.urls import path
from . import views
from . import recipient_reports
from . import foodbank_exports
from . import views_export
from . import foodbank_reports
from . import recipient_exports

urlpatterns = [
    # Main reports dashboard - redirects based on user type
    path('', foodbank_reports.foodbank_reports_dashboard, name='reports_dashboard'),
    
    # FoodBank Reports (New Comprehensive Reports)
    path('foodbank/dashboard/', foodbank_reports.foodbank_reports_dashboard, name='foodbank_reports_dashboard'),
    path('foodbank/donations-revenue/', foodbank_reports.donations_revenue_report, name='donations_revenue_report'),
    path('foodbank/inventory-distribution/', foodbank_reports.inventory_distribution_report, name='inventory_distribution_report'),
    path('foodbank/requests-fulfillment/', foodbank_reports.requests_fulfillment_report, name='requests_fulfillment_report'),
    path('foodbank/subscription-financial/', foodbank_reports.subscription_financial_report, name='subscription_financial_report'),
    path('foodbank/impact-analytics/', foodbank_reports.impact_analytics_report, name='impact_analytics_report'),
    
    # Donor reports
    path('donor/donation-history/', views.donor_donation_history, name='donor_donation_history'),
    path('donor/impact-report/', views.donor_impact_report, name='donor_impact_report'),
    
    # Old Food bank reports (keeping for backward compatibility)
    path('foodbank/donations-received/', views.foodbank_donations_received, name='foodbank_donations_received'),
    path('foodbank/request-fulfillment/', views.foodbank_request_fulfillment, name='foodbank_request_fulfillment'),
    
    # Recipient reports
    path('recipient/comprehensive/', views.reports_dashboard, name='recipient_comprehensive_report'),
    path('recipient/requests-report/', recipient_reports.recipient_requests_report, name='recipient_requests_report'),
    path('recipient/allocations-report/', recipient_reports.recipient_allocations_report, name='recipient_allocations_report'),
    
    # Recipient new export functions
    path('recipient/export/regular-donations/', recipient_exports.recipient_regular_donations_export, name='recipient_regular_donations_export'),
    path('recipient/export/subsidized-donations/', recipient_exports.recipient_subsidized_donations_export, name='recipient_subsidized_donations_export'),
    path('recipient/export/all-allocations/', recipient_exports.recipient_all_allocations_export, name='recipient_all_allocations_export'),
    
    # Admin reports
    path('admin/platform-analytics/', views.admin_platform_analytics, name='admin_platform_analytics'),
    
    # Donor export functions
    path('export/donor-donation-history-csv/', views.export_donor_donation_history_csv, name='export_donor_donation_history_csv'),
    path('export/donor-donation-history-pdf/', views.export_donor_donation_history_pdf, name='export_donor_donation_history_pdf'),
    path('export/donor-impact-pdf/', views.export_donor_impact_pdf, name='export_donor_impact_pdf'),
    
    # Foodbank export functions
    path('export/foodbank-donations-received-csv/', foodbank_exports.export_foodbank_donations_received_csv, name='export_foodbank_donations_received_csv'),
    path('export/foodbank-donations-received-pdf/', views.export_foodbank_donations_received_pdf, name='export_foodbank_donations_received_pdf'),
    path('export/foodbank-request-fulfillment-csv/', foodbank_exports.export_foodbank_request_fulfillment_csv, name='export_foodbank_request_fulfillment_csv'),
    path('export/foodbank-request-fulfillment-pdf/', views.export_foodbank_request_fulfillment_pdf, name='export_foodbank_request_fulfillment_pdf'),
    
    # Recipient export functions
    path('export/recipient-requests-csv/', recipient_reports.export_recipient_requests_csv, name='export_recipient_requests_csv'),
    path('export/recipient-requests-pdf/', recipient_reports.export_recipient_requests_pdf, name='export_recipient_requests_pdf'),
    path('export/recipient-allocations-csv/', recipient_reports.export_recipient_allocations_csv, name='export_recipient_allocations_csv'),
    path('export/recipient-allocations-pdf/', recipient_reports.export_recipient_allocations_pdf, name='export_recipient_allocations_pdf'),
    
    # Recipient completed reports export functions
    path('export/completed-requests-pdf/', views_export.export_completed_requests_pdf, name='export_completed_requests_pdf'),
    path('export/completed-unspecified-pdf/', views_export.export_completed_unspecified_pdf, name='export_completed_unspecified_pdf'),
    path('export/completed-subsidized-pdf/', views_export.export_completed_subsidized_pdf, name='export_completed_subsidized_pdf'),
    
    # Admin export functions
    path('export/admin-platform-analytics-pdf/', views.export_admin_platform_analytics_pdf, name='export_admin_platform_analytics_pdf'),
]
