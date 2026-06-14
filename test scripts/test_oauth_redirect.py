#!/usr/bin/env python
"""
Test OAuth redirect functionality
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

import requests
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from dose.services.gmail_proxy import GmailProxy

def test_oauth_redirect():
    """Test that expired OAuth token triggers proper redirect"""
    print("🔍 Testing OAuth redirect functionality...")

    # Create a test request
    factory = RequestFactory()
    request = factory.get('/admin/gmail/')

    # Add session middleware
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()

    # Add auth middleware
    auth_middleware = AuthenticationMiddleware(lambda r: None)
    auth_middleware.process_request(request)

    # Get a user (should be the demo user we know exists)
    try:
        # Try to find olientAdmin first (has OAuth token), then fallback to any staff user
        user = User.objects.filter(username='olientAdmin').first()
        if not user:
            user = User.objects.filter(is_staff=True).first()
        if not user:
            print("❌ No staff user found - create one first")
            return

        request.user = user
        print(f"✅ Using user: {user.username}")

        # Try to call Gmail API proxy
        print("📧 Testing Gmail API call with expired token...")
        response = GmailProxy.execute_and_save(request, None)

        print(f"📊 Response status: {response.status_code}")
        if response.status_code == 401:
            print("✅ 401 Unauthorized detected - checking error page...")
            content = response.content.decode('utf-8')

            # Check if our improved error handling is working
            if "Re-authenticate with Google" in content:
                print("✅ Improved error handling is working!")
                print("✅ Re-authentication button found in response")
            else:
                print("❌ Improved error handling not found")

            if "/accounts/google/login/?next=/admin/gmail/" in content:
                print("✅ Correct redirect URL to admin Gmail found!")
            elif "/accounts/google/login" in content and "/admin/gmail/" in content:
                print("✅ Admin Gmail redirect URL components found!")
            else:
                print("❌ Admin Gmail redirect URL not found")
                print("Content preview:", content[:500])

        else:
            print(f"⚠️  Unexpected response status: {response.status_code}")
            print("Response preview:", response.content.decode('utf-8')[:200])

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_oauth_redirect()