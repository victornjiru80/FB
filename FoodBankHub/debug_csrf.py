#!/usr/bin/env python
"""
Debug script to test CSRF token generation and validation
Run this to check if CSRF tokens are working properly
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FoodBankHub.settings')
django.setup()

from django.middleware.csrf import get_token
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.middleware.csrf import CsrfViewMiddleware

def test_csrf_token_generation():
    """Test CSRF token generation"""
    print("=== CSRF Token Generation Test ===")
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/login/')
    
    # Add session middleware
    session_middleware = SessionMiddleware(lambda req: None)
    session_middleware.process_request(request)
    request.session.save()
    
    # Generate CSRF token
    token = get_token(request)
    print(f"Generated CSRF Token: {token}")
    print(f"Token Length: {len(token)}")
    print(f"Session Key: {request.session.session_key}")
    
    return token

def test_csrf_settings():
    """Test CSRF settings"""
    print("\n=== CSRF Settings ===")
    print(f"CSRF_COOKIE_AGE: {getattr(settings, 'CSRF_COOKIE_AGE', 'Not set')}")
    print(f"CSRF_COOKIE_SECURE: {getattr(settings, 'CSRF_COOKIE_SECURE', 'Not set')}")
    print(f"CSRF_COOKIE_HTTPONLY: {getattr(settings, 'CSRF_COOKIE_HTTPONLY', 'Not set')}")
    print(f"CSRF_COOKIE_SAMESITE: {getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Not set')}")
    print(f"CSRF_USE_SESSIONS: {getattr(settings, 'CSRF_USE_SESSIONS', 'Not set')}")
    print(f"CSRF_COOKIE_NAME: {getattr(settings, 'CSRF_COOKIE_NAME', 'Not set')}")
    print(f"SESSION_COOKIE_AGE: {getattr(settings, 'SESSION_COOKIE_AGE', 'Not set')}")

if __name__ == "__main__":
    test_csrf_settings()
    test_csrf_token_generation()
    print("\n=== Debug Complete ===")
