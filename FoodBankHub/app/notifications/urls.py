from django.urls import path
from . import views

# Notifications-focused snapshot routes for future module activation.
urlpatterns = [
    path('notifications/mark-read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/acknowledgements/', views.notifications_acknowledgements, name='notifications_acknowledgements'),
    path('notifications/requests/', views.notifications_requests, name='notifications_requests'),
    path('notifications/system-updates/', views.notifications_system_updates, name='notifications_system_updates'),
    path('notifications/foodbank/', views.notifications_foodbank, name='notifications_foodbank'),
    path('notifications/foodbank/system/', views.notifications_foodbank_system, name='notifications_foodbank_system'),
    path('notifications/foodbank/requests/', views.notifications_foodbank_requests, name='notifications_foodbank_requests'),
    path('recipient/notifications/', views.recipient_notifications, name='recipient_notifications'),
]
