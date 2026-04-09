from django.urls import path
from . import views

# Requests-focused snapshot routes for future module activation.
urlpatterns = [
    path('dashboard/request/create/', views.create_foodbank_request, name='create_foodbank_request'),
    path('dashboard/request/<int:pk>/edit/', views.edit_foodbank_request, name='edit_foodbank_request'),
    path('dashboard/request/<int:pk>/delete/', views.delete_foodbank_request, name='delete_foodbank_request'),
    path('dashboard/request/<int:pk>/fulfill/', views.fulfill_foodbank_request, name='fulfill_foodbank_request'),
    path('recipient/create-request/', views.create_request, name='create_request'),
    path('recipient/my-requests/', views.recipient_requests_view, name='recipient_requests_view'),
    path('recipient/my-requests/export/<str:format>/', views.export_recipient_requests, name='export_recipient_requests'),
    path('request/<int:request_id>/detail/', views.request_detail, name='request_detail'),
    path('request/<int:request_id>/fulfill/', views.fulfill_request, name='fulfill_request'),
    path('request/<int:request_id>/partial-fulfill/', views.partial_fulfill_request, name='partial_fulfill_request'),
    path('request/<int:request_id>/decline/', views.decline_request, name='decline_request'),
]
