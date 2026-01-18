#!/usr/bin/env python
"""
Direct OS Ticket Login Test Script
Tests the exact login flow 10 times to see what's happening
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
import time
from dose.models import PassThroughEndpoint

# Get credentials from database
ENDPOINT_ID = 13  # UPDATE THIS to your endpoint ID

print("Loading endpoint from database...", flush=True)
try:
    endpoint = PassThroughEndpoint.objects.get(id=ENDPOINT_ID)
    LOGIN_URL = endpoint.endpoint_url
    if '/scp/login.php' not in LOGIN_URL:
        # Build login URL
        base = LOGIN_URL.split('/scp/')[0].rstrip('/') if '/scp/' in LOGIN_URL else LOGIN_URL.rstrip('/')
        LOGIN_URL = f"{base}/scp/login.php"

    USERNAME = endpoint.auth_username
    PASSWORD = endpoint.auth_password

    print(f"✓ Loaded endpoint {ENDPOINT_ID}", flush=True)
    print(f"  URL: {endpoint.endpoint_url}", flush=True)
    print(f"  Username: {USERNAME}", flush=True)
    print(f"  Password set: {bool(PASSWORD)}", flush=True)

    if not USERNAME or not PASSWORD:
        print(f"❌ ERROR: Endpoint {ENDPOINT_ID} doesn't have auth_username or auth_password set!", flush=True)
        sys.exit(1)

except PassThroughEndpoint.DoesNotExist:
    print(f"❌ ERROR: Endpoint {ENDPOINT_ID} not found!", flush=True)
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR loading endpoint: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

def test_login(iteration, attempt):
    """Test one login attempt"""
    print(f"\n{'='*80}", flush=True)
    print(f"ITERATION {iteration} - ATTEMPT {attempt}", flush=True)
    print(f"{'='*80}\n", flush=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    try:
        # Step 1: GET login page
        print(f"[{iteration}.{attempt}] Step 1: GET login page")
        print(f"  URL: {LOGIN_URL}")
        r1 = session.get(LOGIN_URL, timeout=10)
        print(f"  Status: {r1.status_code}")
        print(f"  Cookies received: {list(session.cookies.keys())}")

        if r1.status_code != 200:
            print(f"  ❌ ERROR: Can't reach login page")
            return None

        # Step 2: Extract CSRF token
        print(f"\n[{iteration}.{attempt}] Step 2: Extract CSRF token")
        soup = BeautifulSoup(r1.text, 'html.parser')
        csrf_input = soup.find("input", {"name": "__CSRFToken__"})

        if not csrf_input:
            print(f"  ❌ ERROR: No CSRF token found")
            print(f"  Page content preview: {r1.text[:500]}")
            return None

        csrf = csrf_input["value"]
        print(f"  ✓ CSRF token: {csrf[:30]}...")

        # Step 3: AJAX POST login
        print(f"\n[{iteration}.{attempt}] Step 3: AJAX POST login")
        payload = {
            "__CSRFToken__": csrf,
            "do": "scplogin",
            "userid": USERNAME,
            "passwd": PASSWORD,
            "ajax": "1"
        }

        print(f"  Payload: {json.dumps({k: v if k != 'passwd' else '***' for k, v in payload.items()}, indent=2)}")

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

        print(f"  Status: {r2.status_code}")
        print(f"  Response headers: {dict(r2.headers)}")
        print(f"  Response text: {r2.text[:500]}")
        print(f"  Cookies after POST: {list(session.cookies.keys())}")

        # Step 4: Check for session cookie
        print(f"\n[{iteration}.{attempt}] Step 4: Check for session cookie")
        cookies = session.cookies.get_dict()
        print(f"  All cookies: {cookies}")

        session_cookie = None
        for cookie_name in ['OSTSESSID', 'SSSESSID']:
            if cookie_name in cookies:
                session_cookie = cookies[cookie_name]
                print(f"  ✓ Found {cookie_name}: {session_cookie[:50]}...")
                break

        if not session_cookie:
            print(f"  ❌ ERROR: No session cookie found")
            print(f"  Available cookies: {list(cookies.keys())}")
            return None

        # Step 5: Test dashboard access
        print(f"\n[{iteration}.{attempt}] Step 5: Test dashboard access")
        dashboard_url = LOGIN_URL.replace('/login.php', '/dashboard.php')
        print(f"  URL: {dashboard_url}")

        r3 = session.get(dashboard_url, timeout=10)
        print(f"  Status: {r3.status_code}")
        print(f"  Response length: {len(r3.text)}")
        print(f"  Response preview: {r3.text[:200]}")

        # Check if access denied
        if 'access denied' in r3.text.lower() or 'login' in r3.text.lower()[:500]:
            print(f"  ❌ ACCESS DENIED - Response contains login/access denied")
        else:
            print(f"  ✓ SUCCESS - Dashboard accessible!")

        return {
            'success': True,
            'session_cookie': session_cookie,
            'cookie_name': 'OSTSESSID' if 'OSTSESSID' in cookies else 'SSSESSID',
            'dashboard_status': r3.status_code,
            'dashboard_accessible': 'access denied' not in r3.text.lower()
        }

    except Exception as e:
        print(f"\n  ❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    try:
        print("\n" + "="*80, flush=True)
        print("OS TICKET LOGIN TEST - 2 ITERATIONS x 10 ATTEMPTS", flush=True)
        print("="*80, flush=True)
        print(f"\nConfiguration:", flush=True)
        print(f"  Endpoint ID: {ENDPOINT_ID}", flush=True)
        print(f"  Login URL: {LOGIN_URL}", flush=True)
        print(f"  Username: {USERNAME}", flush=True)
        print(f"  Password: {'*' * len(PASSWORD)}", flush=True)
        print("\n" + "="*80 + "\n", flush=True)
    except Exception as e:
        print(f"ERROR in main setup: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    results = []

    # Run 2 iterations
    for iteration in range(1, 3):
        # Run 10 attempts per iteration
        for attempt in range(1, 11):
            result = test_login(iteration, attempt)
            if result:
                results.append(result)
            time.sleep(1)  # Small delay between attempts

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total attempts: 20")
    print(f"Successful logins: {len(results)}")
    print(f"Failed: {20 - len(results)}")

    if results:
        print(f"\nSuccessful cookie values (first 3):")
        for i, r in enumerate(results[:3], 1):
            print(f"  {i}. {r['cookie_name']}: {r['session_cookie'][:50]}...")
            print(f"     Dashboard accessible: {r['dashboard_accessible']}")

    print("\n" + "="*80)

