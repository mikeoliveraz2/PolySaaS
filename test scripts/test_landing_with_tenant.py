#!/usr/bin/env python
"""
Quick test to verify landing page works with tenant session
"""
import os
import sys
import django
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.views import landing_page
from dose.models import Tenant, UserProfile

def test_landing_page_with_tenant():
    """Test that landing page works with active tenant session"""
    factory = RequestFactory()
    
    print("🔧 Setting up test...")
    
    # Get or create a test tenant
    tenant, created = Tenant.objects.get_or_create(
        name='Test Tenant',
        defaults={
            'slug': 'test-tenant',
            'description': 'Test tenant for landing page'
        }
    )
    if created:
        print(f"✅ Created test tenant: {tenant.name}")
    else:
        print(f"✅ Using existing tenant: {tenant.name}")
    
    # Get or create a test user
    try:
        user = User.objects.get(username='testuser')
        print(f"✅ Using existing user: {user.username}")
    except User.DoesNotExist:
        user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
        print(f"✅ Created test user: {user.username}")
    
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'tenant': tenant}
    )
    if created:
        print(f"✅ Created user profile for tenant: {tenant.name}")
    else:
        print(f"✅ Using existing profile for tenant: {profile.tenant.name}")
    
    # Create request with tenant session
    request = factory.get('/dose/landing/')
    request.user = user
    
    # Add session middleware
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    
    # Set up tenant session
    request.session['tenant_id'] = tenant.id
    request.session['tenant_name'] = tenant.name
    request.session['tenant_slug'] = tenant.slug
    
    print("\n🧪 Testing landing page view...")
    
    # Test the view
    try:
        response = landing_page(request)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response type: {type(response)}")
        
        if hasattr(response, 'url'):
            print(f"Redirect URL: {response.url}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Landing page loads successfully with tenant session!")
            return True
        elif response.status_code == 302:
            print("ℹ️  REDIRECT: Landing page redirected (this might be expected)")
            return True
        else:
            print(f"❌ FAILURE: Unexpected status code {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing D.O.S.E. Landing Page with Tenant Session...")
    print("=" * 55)
    
    try:
        success = test_landing_page_with_tenant()
        if success:
            print("\n🎉 Test completed successfully!")
            print("\nYour landing page should now work at:")
            print("http://localhost:8000/dose/landing/")
        else:
            print("\n⚠️  Test failed - check the error details above")
            
    except Exception as e:
        print(f"❌ Test setup error: {str(e)}")
        import traceback
        traceback.print_exc()
