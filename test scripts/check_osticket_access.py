#!/usr/bin/env python
"""
Check OS Ticket access - diagnose "access denied" error
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from dose.models import PassThroughEndpoint

print("="*60)
print("OS Ticket Access Diagnosis")
print("="*60)
print()

# Check current user
print("1. Checking user permissions...")
users = User.objects.filter(is_staff=True, is_active=True)
print(f"   Staff users: {users.count()}")
for user in users[:5]:
    print(f"   - {user.username} (email: {user.email}, staff: {user.is_staff}, active: {user.is_active})")

print()
print("2. Checking OS Ticket endpoint configuration...")
endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='osticket')
if endpoints.exists():
    for ep in endpoints:
        print(f"   Endpoint ID: {ep.id}")
        print(f"   Trigger Path: {ep.trigger_path}")
        print(f"   Endpoint URL: {ep.endpoint_url}")
        print(f"   Enabled: {ep.is_enabled}")
        print(f"   Provider: {ep.provider}")
        print(f"   API Auth Type: {ep.api_auth_type}")
        print(f"   Bypass Middleware: {ep.bypass_middleware}")
        print()
else:
    print("   [ERROR] No OS Ticket endpoints found!")

print()
print("3. Testing direct connection to OS Ticket server...")
import requests
try:
    response = requests.get(
        'https://oliverenterprises.app.saasify.cloud/scp/login.php',
        timeout=10,
        verify=False
    )
    print(f"   Status Code: {response.status_code}")
    print(f"   Response Length: {len(response.text)} bytes")

    if 'access denied' in response.text.lower():
        print("   [WARNING] OS Ticket server returned 'access denied' in response")
        print(f"   Response preview: {response.text[:300]}...")
    elif response.status_code == 200:
        print("   [OK] OS Ticket server is reachable")
    else:
        print(f"   [WARNING] Unexpected status code: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Cannot connect to OS Ticket server: {e}")

print()
print("="*60)
print("Diagnosis Complete")
print("="*60)
print()
print("Possible causes of 'access denied':")
print("1. User is not staff (view requires @staff_member_required)")
print("2. OS Ticket server requires authentication/login")
print("3. OAuth2 token missing or expired")
print("4. Session cookies not being forwarded properly")
print()
print("Next steps:")
print("- Make sure you're logged in as a staff user")
print("- Try accessing: http://localhost:8000/admin/osticket/")
print("- Check browser console for errors")
print("- Check Django server logs for [OSTICKET VIEW] messages")

