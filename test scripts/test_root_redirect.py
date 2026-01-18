#!/usr/bin/env python
"""
Test root URL redirect to landing page
"""
import os
import sys
import django
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

def test_root_url_redirect():
    """Test that root URL redirects to landing page"""
    client = Client()
    
    print("🧪 Testing Root URL Redirect...")
    print("=" * 40)
    
    # Test the root URL
    response = client.get('/')
    
    print(f"Response status code: {response.status_code}")
    
    if response.status_code == 302:
        print(f"✅ SUCCESS: Root URL redirects (302)")
        if hasattr(response, 'url'):
            print(f"Redirect URL: {response.url}")
        elif 'Location' in response:
            print(f"Redirect Location: {response['Location']}")
        return True
    else:
        print(f"❌ FAILURE: Expected redirect (302), got {response.status_code}")
        return False

if __name__ == '__main__':
    print("Testing D.O.S.E. Root URL Redirect...")
    print("=" * 50)
    
    try:
        success = test_root_url_redirect()
        if success:
            print("\n🎉 Test completed successfully!")
            print("\nNow when you click 'View Site' from admin, it will redirect to:")
            print("http://localhost:8000/dose/landing/")
            print("\nThis provides a seamless experience from admin to your landing page!")
        else:
            print("\n⚠️  Test failed - check the configuration")
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
