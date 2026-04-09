"""
URL configuration for FoodBankHub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', include('custom_admin.urls')),
    path('secret-backend-admin-panel-2025/', admin.site.urls),  # Hidden Django admin - only for emergency access
    path('', include('authentication.urls')),
    path('reports/', include('reports.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
]

# Custom error handlers (work in both DEBUG and production modes)
handler404 = 'authentication.csrf_views.custom_404_handler'
handler403 = 'authentication.csrf_views.custom_403_handler'
handler500 = 'authentication.csrf_views.custom_500_handler'

# Serve static files in development
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
