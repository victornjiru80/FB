from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views

# Accounts/auth-focused snapshot routes for future module activation.
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/donor/', views.DonorRegistrationView.as_view(), name='register_donor'),
    path('register/foodbank/', views.FoodBankRegistrationView.as_view(), name='register_foodbank'),
    path('register/recipient/', views.RecipientRegistrationView.as_view(), name='register_recipient'),
    path('register/admin/', views.AdminRegistrationView.as_view(), name='register_admin'),
    path('registration/pending/', TemplateView.as_view(template_name='authentication/registration_pending.html'), name='registration_pending'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='authentication/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='authentication/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='authentication/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='authentication/password_reset_complete.html'), name='password_reset_complete'),
]
