#!/usr/bin/env python
"""
Test the admin Gmail view with session to see what happens.
"""
import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

def test_admin_gmail_with_session():
    """Test admin Gmail view with proper session setup"""
    from django.test import Client
    from django.contrib.auth.models import User

    print("=== Testing Admin Gmail View with Session ===")

    try:
        # Get the user
        user = User.objects.get(username='olientAdmin')
        print(f"✅ Found user: {user.username}")

        # Create a test client and login
        client = Client()
        client.force_login(user)
        print("✅ User logged in to test client")

        # Test the admin Gmail URL
        print("\n🧪 Testing /admin/gmail/ with logged-in user...")
        response = client.get('/admin/gmail/')

        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response type: {type(response)}")

        if hasattr(response, 'content'):
            content = response.content.decode('utf-8') if isinstance(response.content, bytes) else str(response.content)

            # Check what type of response we got
            if response.status_code == 200:
                print("✅ Status 200 - Admin view is working")

                # Check if it's our enhanced error page
                if 'Re-authenticate with Google' in content:
                    print("🎉 ENHANCED ERROR PAGE IS WORKING!")
                    print("✅ Found 'Re-authenticate with Google' button")
                elif 'Gmail API Error' in content and 'Error 401' in content:
                    print("❌ Basic error page - enhanced handling not working")
                elif 'Gmail Integration' in content:
                    print("📧 Gmail interface loaded (OAuth token might be working)")
                else:
                    print("❓ Unknown response content")
                    print(f"📄 Content sample: {content[:300]}...")

            elif response.status_code == 401:
                if 'Re-authenticate with Google' in content:
                    print("🎉 ENHANCED 401 ERROR PAGE IS WORKING!")
                else:
                    print("❌ Basic 401 error page")

            else:
                print(f"⚠️  Unexpected status code: {response.status_code}")
                print(f"📄 Content sample: {content[:300]}...")

    except User.DoesNotExist:
        print("❌ User 'olientAdmin' not found")
    except Exception as e:
        print(f"❌ Error testing admin view: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_admin_gmail_with_session()