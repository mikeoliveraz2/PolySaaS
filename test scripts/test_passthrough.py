"""
Test and debug passthrough endpoints
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
import requests

def test_passthrough():
    print("=" * 80)
    print("PASSTHROUGH ENDPOINT CONFIGURATION")
    print("=" * 80)

    endpoints = PassThroughEndpoint.objects.all()
    print(f"\nTotal endpoints: {endpoints.count()}")

    for endpoint in endpoints:
        print(f"\n{'='*60}")
        print(f"ID: {endpoint.id}")
        print(f"Trigger Path: {endpoint.trigger_path}")
        print(f"Endpoint URL: {endpoint.endpoint_url}")
        print(f"Enabled: {endpoint.is_enabled}")
        if hasattr(endpoint, 'tenant'):
            print(f"Tenant: {endpoint.tenant}")

    print("\n" + "=" * 80)
    print("TESTING MIDDLEWARE FLOW")
    print("=" * 80)

    # Test OsTicket passthrough
    test_url = "http://localhost:8000/admin/osticket/"
    print(f"\nTest URL: {test_url}")
    print("Making request...")

    try:
        response = requests.get(test_url, allow_redirects=False)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content Length: {len(response.content)} bytes")

        if 300 <= response.status_code < 400:
            print(f"Redirect Location: {response.headers.get('Location')}")

        if response.status_code == 422:
            print("\n⚠️  422 Unprocessable Content - Let's check why:")
            print(f"First 500 chars of response:\n{response.text[:500]}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test Gmail passthrough
    test_url = "http://localhost:8000/admin/gmail/"
    print(f"\n\nTest URL: {test_url}")
    print("Making request...")

    try:
        response = requests.get(test_url, allow_redirects=False)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content Length: {len(response.content)} bytes")

        if 300 <= response.status_code < 400:
            print(f"Redirect Location: {response.headers.get('Location')}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_passthrough()
