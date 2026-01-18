#!/usr/bin/env python
"""
Fix OS Ticket endpoint auth configuration - remove OAuth2 requirement
OS Ticket uses session-based login, not OAuth2
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*60)
print("Fixing OS Ticket Auth Configuration")
print("="*60)
print()

# Find all OS Ticket endpoints
endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='osticket')

if not endpoints.exists():
    print("[ERROR] No OS Ticket endpoints found!")
    exit(1)

for ep in endpoints:
    print(f"Found endpoint ID: {ep.id}")
    print(f"  Trigger Path: {ep.trigger_path}")
    print(f"  Current API Auth Type: {ep.api_auth_type}")
    print(f"  Current Provider: {ep.provider}")
    print()

    # OS Ticket uses session-based login, not OAuth2
    # Remove OAuth2 requirement - set to empty string or 'api_key' (least intrusive)
    if ep.api_auth_type in ['oauth2', 'bearer']:
        print(f"  [FIXING] Removing OAuth2 requirement...")
        # Set to empty string or a valid choice that won't interfere
        # Since OS Ticket uses session cookies, we don't need API auth
        ep.api_auth_type = ''  # Empty string (if allowed) or use 'api_key' as placeholder
        ep.provider = 'custom'  # Keep as custom
        try:
            ep.save()
            print(f"  [OK] Updated - API Auth Type: '' (session-based)")
        except:
            # If empty not allowed, try 'api_key' as placeholder
            ep.api_auth_type = 'api_key'
            ep.save()
            print(f"  [OK] Updated - API Auth Type: 'api_key' (placeholder, not used)")
    else:
        print(f"  [OK] Already configured correctly")

print()
print("="*60)
print("Configuration Updated!")
print("="*60)
print()
print("OS Ticket now uses session-based authentication (cookies)")
print("No OAuth2 token required - login via form with username/password")
print()
print("Try accessing OS Ticket again: http://localhost:8000/admin/osticket/")

