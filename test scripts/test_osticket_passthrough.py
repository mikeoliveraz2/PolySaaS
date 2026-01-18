#!/usr/bin/env python
"""
Quick test script to verify OSTicket passthrough is working
Tests the generic_html_passthrough function directly
"""

import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from dose.passthrough_views import generic_html_passthrough

# Create a fake request
factory = RequestFactory()
request = factory.get('/admin/passthrough/osticket/')

# Create a test user
User.objects.filter(username='testuser').delete()
user = User.objects.create_user(username='testuser', password='testpass')
request.user = user

print("\n" + "="*120)
print("TESTING OSTicket PASSTHROUGH")
print("="*120 + "\n")

try:
    print("[TEST] Calling generic_html_passthrough()...")
    response = generic_html_passthrough(
        request=request,
        real_endpoint="https://oliverenterprises.app.saasify.cloud/scp/dashboard.php",
        real_domain="https://oliverenterprises.app.saasify.cloud",
        real_path="/scp/",
        proxy_path="/admin/passthrough/osticket/",
        service_name="OSTicket"
    )

    print(f"[TEST] Response status: {response.status_code}")
    print(f"[TEST] Response type: {type(response)}")
    print(f"[TEST] Response content type: {response.get('Content-Type', 'N/A')}")
    print(f"[TEST] Response content length: {len(response.content)} bytes")

    # Check if content has absolute URLs
    content_str = response.content.decode('utf-8')

    print(f"\n[TEST] Checking for absolute URLs in response:")
    print(f"  - Contains 'https://oliverenterprises.app.saasify.cloud/scp/css/': {('https://oliverenterprises.app.saasify.cloud/scp/css/' in content_str)}")
    print(f"  - Contains 'https://oliverenterprises.app.saasify.cloud/scp/login.php': {('https://oliverenterprises.app.saasify.cloud/scp/login.php' in content_str)}")
    print(f"  - Contains relative 'css/': {('css/' in content_str and 'https://oliverenterprises.app.saasify.cloud/scp/css/' not in content_str)}")

    # Check for _skip_url_mapping flag
    has_skip_flag = getattr(response, '_skip_url_mapping', False)
    print(f"\n[TEST] Response marked to skip middleware URL mapping: {has_skip_flag}")

    print("\n[TEST] ✅ Passthrough test completed successfully!")

except Exception as e:
    print(f"\n[TEST] ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*120 + "\n")
