#!/usr/bin/env python
"""
Test the Gmail admin integration directly to see what's happening.
"""
import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

def test_gmail_admin_directly():
    """Test Gmail admin view directly"""
    from django.test import RequestFactory
    from django.contrib.auth.models import User
    from dose.admin_views import admin_gmail_view

    print("=== Testing Gmail Admin View Directly ===")

    # Create a test request
    factory = RequestFactory()
    request = factory.get('/admin/gmail/')

    # Get a test user
    try:
        user = User.objects.get(username='olientAdmin')
        request.user = user
        print(f"✅ Found user: {user.username}")

        # Test the admin view
        print("\n🧪 Testing admin_gmail_view...")
        response = admin_gmail_view(request)
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response type: {type(response)}")

        if hasattr(response, 'content'):
            content = response.content.decode('utf-8') if isinstance(response.content, bytes) else str(response.content)
            if len(content) > 500:
                print(f"📄 Response content (first 500 chars): {content[:500]}...")
            else:
                print(f"📄 Response content: {content}")

        # Check if it's our enhanced error page
        if response.status_code == 401:
            print("🔍 Got 401 - checking if it's our enhanced error page...")
            if 'Re-authenticate with Google' in content:
                print("✅ Enhanced OAuth error page is working!")
            else:
                print("❌ Basic error page - enhanced error handling not working")

    except User.DoesNotExist:
        print("❌ User 'olientAdmin' not found")
    except Exception as e:
        print(f"❌ Error testing admin view: {e}")

if __name__ == "__main__":
    test_gmail_admin_directly()