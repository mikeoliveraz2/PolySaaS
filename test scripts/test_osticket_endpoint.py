#!/usr/bin/env python
"""
Test OSTicket endpoint connectivity and response
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
import requests

print("\n" + "="*80)
print("OSTicket Endpoint Diagnostic")
print("="*80 + "\n")

# Find endpoint
endpoint = PassThroughEndpoint.objects.filter(
    trigger_path='/admin/osticket/',
    is_enabled=True
).first()

if not endpoint:
    print("❌ ERROR: No OSTicket endpoint configured!")
    print("\nTo configure, run: python setup_osticket_endpoint.py")
    sys.exit(1)

print(f"✓ Found endpoint configuration:")
print(f"  Trigger Path: {endpoint.trigger_path}")
print(f"  Endpoint URL: {endpoint.endpoint_url}")
print(f"  Enabled: {endpoint.is_enabled}")
print(f"\nTesting connectivity...\n")

try:
    response = requests.get(
        endpoint.endpoint_url,
        timeout=10,
        verify=False,
        headers={'User-Agent': 'Mozilla/5.0'},
        allow_redirects=True
    )

    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.text)} bytes")
    print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")

    # Try to parse
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('title')
    body = soup.find('body')

    print(f"\nHTML Analysis:")
    print(f"  Title: {title.string if title else 'Not found'}")
    print(f"  Body Tag: {'Found' if body else 'Not found'}")

    if response.status_code == 422:
        print(f"\n⚠️  Got 422 Unprocessable Entity")
        print(f"   This usually means OSTicket rejected the request due to:")
        print(f"   - Missing authentication")
        print(f"   - Invalid request format")
        print(f"   - CSRF token validation failure")
        print(f"\n   First 500 chars of response:")
        print(f"   {response.text[:500]}\n")

    if response.status_code == 200:
        print(f"\n✓ OSTicket endpoint is responding correctly!")
        print(f"  Content should be displayed in admin interface at /admin/osticket/")
    else:
        print(f"\n⚠️  Endpoint returned status {response.status_code}")
        print(f"   This response will still be displayed in the admin interface.")

except requests.exceptions.Timeout:
    print(f"❌ ERROR: Request timed out after 10 seconds")
    print(f"   Check if {endpoint.endpoint_url} is reachable")
except requests.exceptions.ConnectionError as e:
    print(f"❌ ERROR: Connection failed: {e}")
    print(f"   Check if {endpoint.endpoint_url} is accessible")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
