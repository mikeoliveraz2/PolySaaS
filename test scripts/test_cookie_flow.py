#!/usr/bin/env python
"""
Test cookie flow - verify cookies are being saved and retrieved correctly
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
import json

ENDPOINT_ID = 13
endpoint = PassThroughEndpoint.objects.get(id=ENDPOINT_ID)

print("="*80)
print("COOKIE FLOW TEST")
print("="*80)
print(f"\nEndpoint ID: {ENDPOINT_ID}")
print(f"Endpoint URL: {endpoint.endpoint_url}")
print(f"Trigger Path: {endpoint.trigger_path}")
print(f"\nAuth Username: {endpoint.auth_username}")
print(f"Auth Password: {'*' * len(endpoint.auth_password) if endpoint.auth_password else 'NOT SET'}")

print(f"\n{'='*80}")
print("CHECKING discovered_subpaths")
print(f"{'='*80}")
print(f"discovered_subpaths type: {type(endpoint.discovered_subpaths)}")
print(f"discovered_subpaths value: {endpoint.discovered_subpaths}")

if endpoint.discovered_subpaths:
    if 'cookies' in endpoint.discovered_subpaths:
        cookies = endpoint.discovered_subpaths['cookies']
        print(f"\n✓ Cookies found in discovered_subpaths:")
        for name, value in cookies.items():
            print(f"  {name}: {value[:50]}...")

        # Check for session cookie
        session_cookie = None
        for name in ['OSTSESSID', 'SSSESSID']:
            if name in cookies:
                session_cookie = (name, cookies[name])
                break

        if session_cookie:
            print(f"\n✓ Session cookie found: {session_cookie[0]}")
        else:
            print(f"\n✗ No session cookie (OSTSESSID/SSSESSID) found in cookies")
    else:
        print(f"\n✗ No 'cookies' key in discovered_subpaths")
        print(f"  Keys in discovered_subpaths: {list(endpoint.discovered_subpaths.keys())}")
else:
    print(f"\n✗ discovered_subpaths is empty or None")

print(f"\n{'='*80}")
print("CHECKING polysniffer_debug_output")
print(f"{'='*80}")
if endpoint.polysniffer_debug_output:
    try:
        debug_data = json.loads(endpoint.polysniffer_debug_output)
        print(f"Last run: {debug_data.get('timestamp', 'N/A')}")
        print(f"Method: {debug_data.get('method', 'N/A')}")
        print(f"Login URL: {debug_data.get('login_url', 'N/A')}")
        if 'cookies_captured' in debug_data:
            print(f"Cookies captured: {list(debug_data['cookies_captured'].keys())}")
    except:
        print(f"Debug output (raw): {endpoint.polysniffer_debug_output[:500]}")
else:
    print("No debug output")

print(f"\n{'='*80}")
print("CHECKING persistent session")
print(f"{'='*80}")
from dose.osticket_admin import get_osticket_session
session = get_osticket_session()
print(f"Session cookies: {dict(session.cookies)}")

print(f"\n{'='*80}")
print("RECOMMENDATION")
print(f"{'='*80}")
if endpoint.discovered_subpaths and 'cookies' in endpoint.discovered_subpaths:
    cookies = endpoint.discovered_subpaths['cookies']
    if any(name in cookies for name in ['OSTSESSID', 'SSSESSID']):
        print("✓ Cookies are saved correctly")
        print("  → Try clicking 'Auto-Login' again to refresh the cookie")
        print("  → Then immediately access OS Ticket through passthrough")
    else:
        print("✗ Cookies saved but no session cookie found")
        print("  → Login may have failed - check credentials")
else:
    print("✗ No cookies found in discovered_subpaths")
    print("  → Click 'Auto-Login' button to capture cookies")

