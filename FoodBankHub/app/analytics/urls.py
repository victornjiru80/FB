from django.urls import path
from . import views
from . import views_export

# Analytics/reporting snapshot routes for future module activation.
urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('dashboard/', views.reports_dashboard, name='reports_dashboard_revamped'),
    path('donor-donation-history/', views.donor_donation_history, name='donor_donation_history_report'),
    path('donor-impact/', views.donor_impact_report, name='donor_impact_report'),
    path('foodbank-donations-received/', views.foodbank_donations_received, name='foodbank_donations_received'),
    path('foodbank-request-fulfillment/', views.foodbank_request_fulfillment, name='foodbank_request_fulfillment'),
    path('admin-platform-analytics/', views.admin_platform_analytics, name='admin_platform_analytics'),
    path('export/<str:report_type>/<str:format_type>/', views_export.export_report_data, name='export_report_data'),
]
