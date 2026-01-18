"""
Test passthrough with authenticated session
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def test_authenticated_passthrough():
    print("=" * 80)
    print("TESTING PASSTHROUGH WITH AUTHENTICATED SESSION")
    print("=" * 80)

    # Create a test client
    client = Client()

    # Get or create a superuser
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("No superuser found, creating one...")
        user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')

    print(f"\nLogging in as: {user.username}")
    client.force_login(user)

    # Test OsTicket passthrough
    print("\n" + "=" * 60)
    print("Testing OsTicket Passthrough")
    print("=" * 60)
    test_path = "/admin/osticket/"
    print(f"Path: {test_path}")

    response = client.get(test_path, follow=False)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.get('Content-Type', 'N/A')}")
    print(f"Content Length: {len(response.content)} bytes")

    if hasattr(response, 'headers'):
        if 'Location' in response.headers:
            print(f"Redirect Location: {response.headers['Location']}")

    if response.status_code == 422:
        print("\n⚠️  422 Status - Checking response content:")
        print(f"First 1000 chars:\n{response.content.decode('utf-8', errors='ignore')[:1000]}")
    elif response.status_code == 200:
        print("\n✅ 200 OK - Checking response content:")
        print(f"First 500 chars:\n{response.content.decode('utf-8', errors='ignore')[:500]}")

    # Test Gmail passthrough
    print("\n" + "=" * 60)
    print("Testing Gmail Passthrough")
    print("=" * 60)
    test_path = "/admin/gmail/"
    print(f"Path: {test_path}")

    response = client.get(test_path, follow=False)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.get('Content-Type', 'N/A')}")
    print(f"Content Length: {len(response.content)} bytes")

    if hasattr(response, 'headers'):
        if 'Location' in response.headers:
            print(f"Redirect Location: {response.headers['Location']}")

if __name__ == "__main__":
    test_authenticated_passthrough()
