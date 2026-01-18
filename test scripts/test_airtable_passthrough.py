#!/usr/bin/env python
"""
Test Airtable passthrough view
"""
import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.test import APIClient

# Create test user if doesn't exist
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'is_staff': True, 'is_superuser': True}
)
if created:
    user.set_password('testpass')
    user.save()
    print(f"✓ Created test user: testuser")

# Create API client and authenticate
client = APIClient()
client.force_authenticate(user=user)

print("\n" + "="*80)
print("TESTING AIRTABLE PASSTHROUGH")
print("="*80 + "\n")

# Test the Airtable endpoint
url = "http://localhost:8000/pt/admin/airtable/"
print(f"Testing URL: {url}")
print()

try:
    response = requests.get(url, cookies=client.cookies, timeout=10)
    print(f"✓ Response Status: {response.status_code}")
    print(f"✓ Content-Type: {response.headers.get('content-type', 'unknown')}")
    print(f"✓ Content Length: {len(response.text)} bytes")
    print()

    # Check if API interceptor was injected
    if "[PolySaaS] API Interceptor" in response.text:
        print("✓ API Interceptor INJECTED successfully!")
        print("✓ Airtable SPA API calls will be proxied through Django")
    else:
        print("⚠ API Interceptor NOT found in response")
        print("  This is OK if Airtable returns JSON or non-HTML content")

    print()

    # Show first 500 chars of response
    if len(response.text) > 500:
        print(f"Response Preview (first 500 chars):")
        print("-" * 80)
        print(response.text[:500])
        print("-" * 80)
    else:
        print(f"Full Response:")
        print("-" * 80)
        print(response.text)
        print("-" * 80)

except Exception as e:
    print(f"✗ Error: {e}")

print()
print("="*80)
print("TEST COMPLETE")
print("="*80)
