#!/usr/bin/env python
"""
Simple OS Ticket Login Test - Reads from database
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

import requests
from bs4 import BeautifulSoup
import json
from dose.models import PassThroughEndpoint

# Get from database
ENDPOINT_ID = 13
endpoint = PassThroughEndpoint.objects.get(id=ENDPOINT_ID)

LOGIN_URL = endpoint.endpoint_url
if '/scp/login.php' not in LOGIN_URL:
    base = LOGIN_URL.split('/scp/')[0].rstrip('/') if '/scp/' in LOGIN_URL else LOGIN_URL.rstrip('/')
    LOGIN_URL = f"{base}/scp/login.php"

USERNAME = endpoint.auth_username
PASSWORD = endpoint.auth_password

print(f"Loaded from endpoint {ENDPOINT_ID}:")
print(f"  URL: {LOGIN_URL}")
print(f"  Username: {USERNAME}")
print(f"  Password: {'*' * len(PASSWORD) if PASSWORD else 'NOT SET'}\n")

def test_login():
    import sys
    sys.stdout.write(f"\n{'='*80}\n")
    sys.stdout.write("OS TICKET LOGIN TEST\n")
    sys.stdout.write(f"{'='*80}\n\n")
    sys.stdout.flush()

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    try:
        # Step 1: GET login page
        print(f"[1] GET login page: {LOGIN_URL}", flush=True)
        r1 = session.get(LOGIN_URL, timeout=10)
        print(f"    Status: {r1.status_code}", flush=True)
        print(f"    Cookies: {list(session.cookies.keys())}", flush=True)

        if r1.status_code != 200:
            print(f"    ❌ ERROR: Can't reach login page")
            return

        # Step 2: Extract CSRF
        print(f"\n[2] Extract CSRF token")
        soup = BeautifulSoup(r1.text, 'html.parser')
        csrf_input = soup.find("input", {"name": "__CSRFToken__"})

        if not csrf_input:
            print(f"    ❌ ERROR: No CSRF token")
            return

        csrf = csrf_input["value"]
        print(f"    ✓ CSRF: {csrf[:30]}...")

        # Step 3: AJAX POST
        print(f"\n[3] AJAX POST login")
        payload = {
            "__CSRFToken__": csrf,
            "do": "scplogin",
            "userid": USERNAME,
            "passwd": PASSWORD,
            "ajax": "1"
        }

        r2 = session.post(
            LOGIN_URL,
            data=payload,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": LOGIN_URL
            },
            timeout=10
        )

        print(f"    Status: {r2.status_code}")
        print(f"    Response: {r2.text[:300]}")
        print(f"    Cookies after POST: {list(session.cookies.keys())}")
        print(f"    Cookie values: {session.cookies.get_dict()}")

        # Step 4: Check cookie
        cookies = session.cookies.get_dict()
        session_cookie = None
        for name in ['OSTSESSID', 'SSSESSID']:
            if name in cookies:
                session_cookie = cookies[name]
                print(f"\n[4] ✓ Found {name}: {session_cookie[:50]}...")
                break

        if not session_cookie:
            print(f"\n[4] ❌ No session cookie found!")
            return

        # Step 5: Test dashboard
        print(f"\n[5] Test dashboard access")
        dashboard_url = LOGIN_URL.replace('/login.php', '/dashboard.php')
        r3 = session.get(dashboard_url, timeout=10)
        print(f"    Status: {r3.status_code}")
        print(f"    Response length: {len(r3.text)}")

        if 'access denied' in r3.text.lower()[:500]:
            print(f"    ❌ ACCESS DENIED")
        elif 'login' in r3.text.lower()[:500]:
            print(f"    ❌ REDIRECTED TO LOGIN")
        else:
            print(f"    ✓ SUCCESS - Dashboard accessible!")
            print(f"    Response preview: {r3.text[:200]}")

    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if not USERNAME or not PASSWORD:
        print("❌ ERROR: Username or password not set in endpoint!")
        sys.exit(1)

    print(f"\n{'='*80}")
    print("STARTING 10 LOGIN TESTS")
    print(f"{'='*80}\n")

    # Run 10 times
    for i in range(1, 11):
        print(f"\n\n{'#'*80}")
        print(f"ATTEMPT {i}/10")
        print(f"{'#'*80}")
        test_login()
        import time
        if i < 10:
            time.sleep(2)

    print(f"\n\n{'='*80}")
    print("ALL TESTS COMPLETE")
    print(f"{'='*80}\n")

