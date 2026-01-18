#!/usr/bin/env python
"""
Test landing page redirect logic
"""
import os
import sys
import django
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.views import landing_page
from dose.models import Tenant, UserProfile

def test_landing_page_redirect():
    """Test that landing page redirects when no tenant session"""
    factory = RequestFactory()
    
    # Create a test user
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
    
    # Create request without tenant session
    request = factory.get('/dose/landing/')
    request.user = user
    
    # Add session middleware
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    
    # Test the view
    response = landing_page(request)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response type: {type(response)}")
    
    if hasattr(response, 'url'):
        print(f"Redirect URL: {response.url}")
    
    # Test should show a redirect (302) to login
    if response.status_code == 302:
        print("✅ SUCCESS: Landing page correctly redirects when no tenant session")
        return True
    else:
        print("❌ FAILURE: Landing page should redirect when no tenant session")
        return False

if __name__ == '__main__':
    print("Testing D.O.S.E. Landing Page Redirect Logic...")
    print("=" * 50)
    
    try:
        success = test_landing_page_redirect()
        if success:
            print("\n🎉 Test completed successfully!")
            print("\nNow when you visit http://localhost:8000/dose/landing/ without")
            print("an active tenant session, it should redirect to:")
            print("http://localhost:8000/dose/login/?next=/dose/landing/")
        else:
            print("\n⚠️  Test failed - check the logic")
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
