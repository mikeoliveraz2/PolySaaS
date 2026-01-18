#!/usr/bin/env python
"""
Direct test: Use the saved cookie to access OS Ticket dashboard
This will tell us if the cookie is valid or if there's another issue
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

import requests
from dose.models import PassThroughEndpoint
from urllib.parse import urlparse

ENDPOINT_ID = 13
endpoint = PassThroughEndpoint.objects.get(id=ENDPOINT_ID)

print("="*80)
print("DIRECT OS TICKET COOKIE TEST")
print("="*80)

# Get saved cookies
if not endpoint.discovered_subpaths or 'cookies' not in endpoint.discovered_subpaths:
    print("\n❌ ERROR: No cookies found in discovered_subpaths")
    print("   → Click 'Auto-Login' button first to capture cookies")
    sys.exit(1)

cookies = endpoint.discovered_subpaths['cookies']
print(f"\n✓ Found {len(cookies)} cookies in discovered_subpaths:")
for name, value in cookies.items():
    print(f"  {name}: {value[:50]}...")

# Find session cookie
session_cookie_name = None
session_cookie_value = None
for name in ['OSTSESSID', 'SSSESSID']:
    if name in cookies:
        session_cookie_name = name
        session_cookie_value = cookies[name]
        break

if not session_cookie_value:
    print("\n❌ ERROR: No session cookie (OSTSESSID/SSSESSID) found")
    sys.exit(1)

print(f"\n✓ Using session cookie: {session_cookie_name}")

# Build dashboard URL
login_url = endpoint.endpoint_url
if '/scp/login.php' not in login_url:
    base = login_url.split('/scp/')[0].rstrip('/') if '/scp/' in login_url else login_url.rstrip('/')
    login_url = f"{base}/scp/login.php"

dashboard_url = login_url.replace('/login.php', '/dashboard.php')
print(f"\nTesting dashboard URL: {dashboard_url}")

# Test 1: Use requests.Session with cookie set
print(f"\n{'='*80}")
print("TEST 1: Using requests.Session with cookie")
print(f"{'='*80}")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

# Set all cookies
for name, value in cookies.items():
    session.cookies.set(name, value)

print(f"Session cookies before request: {dict(session.cookies)}")

try:
    r = session.get(dashboard_url, timeout=10, verify=False)
    print(f"Status: {r.status_code}")
    print(f"Response URL: {r.url}")
    print(f"Response length: {len(r.text)}")

    if 'access denied' in r.text.lower()[:1000]:
        print("❌ ACCESS DENIED detected in response")
        print(f"Response preview: {r.text[:500]}")
    elif 'login' in r.text.lower()[:1000] and 'dashboard' not in r.text.lower()[:1000]:
        print("❌ REDIRECTED TO LOGIN")
        print(f"Response preview: {r.text[:500]}")
    else:
        print("✓ SUCCESS - Dashboard accessible!")
        print(f"Response preview: {r.text[:200]}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Manually set Cookie header
print(f"\n{'='*80}")
print("TEST 2: Using manual Cookie header")
print(f"{'='*80}")

session2 = requests.Session()
session2.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": dashboard_url,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})

# Manually construct Cookie header
cookie_header_parts = [f"{name}={value}" for name, value in cookies.items()]
session2.headers['Cookie'] = '; '.join(cookie_header_parts)

print(f"Cookie header: {session2.headers['Cookie'][:100]}...")

try:
    r2 = session2.get(dashboard_url, timeout=10, verify=False)
    print(f"Status: {r2.status_code}")
    print(f"Response URL: {r2.url}")
    print(f"Response length: {len(r2.text)}")

    if 'access denied' in r2.text.lower()[:1000]:
        print("❌ ACCESS DENIED detected in response")
        print(f"Response preview: {r2.text[:500]}")
    elif 'login' in r2.text.lower()[:1000] and 'dashboard' not in r2.text.lower()[:1000]:
        print("❌ REDIRECTED TO LOGIN")
        print(f"Response preview: {r2.text[:500]}")
    else:
        print("✓ SUCCESS - Dashboard accessible!")
        print(f"Response preview: {r2.text[:200]}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check if cookie is expired or invalid
print(f"\n{'='*80}")
print("TEST 3: Fresh login to compare")
print(f"{'='*80}")

print("Performing fresh login to get a new cookie...")
from bs4 import BeautifulSoup

session3 = requests.Session()
session3.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

try:
    # Get login page
    r_login = session3.get(login_url, timeout=10, verify=False)
    soup = BeautifulSoup(r_login.text, 'html.parser')
    csrf_input = soup.find("input", {"name": "__CSRFToken__"})

    if not csrf_input:
        print("❌ Can't get CSRF token")
    else:
        csrf = csrf_input["value"]

        # Login
        payload = {
            "__CSRFToken__": csrf,
            "do": "scplogin",
            "userid": endpoint.auth_username,
            "passwd": endpoint.auth_password,
            "ajax": "1"
        }

        r_post = session3.post(
            login_url,
            data=payload,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": login_url
            },
            timeout=10,
            verify=False
        )

        # Get fresh cookie
        fresh_cookies = session3.cookies.get_dict()
        fresh_session_cookie = None
        for name in ['OSTSESSID', 'SSSESSID']:
            if name in fresh_cookies:
                fresh_session_cookie = (name, fresh_cookies[name])
                break

        if fresh_session_cookie:
            print(f"✓ Fresh {fresh_session_cookie[0]} cookie: {fresh_session_cookie[1][:50]}...")

            # Compare with saved cookie
            if session_cookie_value == fresh_session_cookie[1]:
                print("✓ Saved cookie matches fresh cookie - cookie is still valid")
            else:
                print("❌ Saved cookie is DIFFERENT from fresh cookie - cookie may be expired!")
                print(f"  Saved: {session_cookie_value[:50]}...")
                print(f"  Fresh: {fresh_session_cookie[1][:50]}...")

            # Test fresh cookie
            print("\nTesting fresh cookie on dashboard...")
            r_dash = session3.get(dashboard_url, timeout=10, verify=False)
            if 'access denied' in r_dash.text.lower()[:1000]:
                print("❌ ACCESS DENIED even with fresh cookie!")
                print("   → This suggests OS Ticket is checking something else (IP, User-Agent, etc.)")
            else:
                print("✓ Fresh cookie works - saved cookie may be expired")
        else:
            print("❌ Login failed - no session cookie received")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print("TEST COMPLETE")
print(f"{'='*80}")

