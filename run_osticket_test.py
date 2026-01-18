#!/usr/bin/env python
"""
OS Ticket Login Test - Simple version that writes to file
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
import time
from dose.models import PassThroughEndpoint

# Output file
OUTPUT_FILE = 'osticket_test_output.txt'

def log(msg, file_handle):
    """Write to both console and file"""
    print(msg, flush=True)
    file_handle.write(msg + '\n')
    file_handle.flush()

# Get credentials
ENDPOINT_ID = 13
endpoint = PassThroughEndpoint.objects.get(id=ENDPOINT_ID)

LOGIN_URL = endpoint.endpoint_url
if '/scp/login.php' not in LOGIN_URL:
    base = LOGIN_URL.split('/scp/')[0].rstrip('/') if '/scp/' in LOGIN_URL else LOGIN_URL.rstrip('/')
    LOGIN_URL = f"{base}/scp/login.php"

USERNAME = endpoint.auth_username
PASSWORD = endpoint.auth_password

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    log("="*80, f)
    log("OS TICKET LOGIN TEST - 10 ITERATIONS", f)
    log("="*80, f)
    log("", f)
    log(f"Login URL: {LOGIN_URL}", f)
    log(f"Username: {USERNAME}", f)
    log(f"Password: {'*' * len(PASSWORD) if PASSWORD else 'NOT SET'}", f)
    log("", f)

    results = []

    for iteration in range(1, 11):
        log(f"\n{'#'*80}", f)
        log(f"ITERATION {iteration}/10", f)
        log(f"{'#'*80}", f)

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        try:
            # Step 1: GET login
            log(f"\n[1] GET {LOGIN_URL}", f)
            r1 = session.get(LOGIN_URL, timeout=10, verify=False)
            log(f"    Status: {r1.status_code}", f)
            log(f"    Cookies: {list(session.cookies.keys())}", f)

            if r1.status_code != 200:
                log(f"    ❌ ERROR: Can't reach login page", f)
                results.append(('FAIL', 'Can\'t reach login'))
                continue

            # Step 2: Extract CSRF
            log(f"\n[2] Extract CSRF token", f)
            soup = BeautifulSoup(r1.text, 'html.parser')
            csrf_input = soup.find("input", {"name": "__CSRFToken__"})

            if not csrf_input:
                log(f"    ❌ ERROR: No CSRF token found", f)
                log(f"    Response preview: {r1.text[:500]}", f)
                results.append(('FAIL', 'No CSRF token'))
                continue

            csrf = csrf_input["value"]
            log(f"    ✓ CSRF: {csrf[:30]}...", f)

            # Step 3: AJAX POST
            log(f"\n[3] AJAX POST login", f)
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
                timeout=10,
                verify=False
            )

            log(f"    Status: {r2.status_code}", f)
            log(f"    Response: {r2.text[:300]}", f)
            log(f"    Cookies: {session.cookies.get_dict()}", f)

            # Step 4: Check session cookie
            cookies = session.cookies.get_dict()
            session_cookie_name = None
            session_cookie_value = None

            for name in ['OSTSESSID', 'SSSESSID']:
                if name in cookies:
                    session_cookie_name = name
                    session_cookie_value = cookies[name]
                    break

            if not session_cookie_value:
                log(f"\n[4] ❌ No session cookie found!", f)
                results.append(('FAIL', 'No session cookie'))
                continue

            log(f"\n[4] ✓ Found {session_cookie_name}: {session_cookie_value[:50]}...", f)

            # Step 5: Test dashboard
            log(f"\n[5] Test dashboard access", f)
            dashboard_url = LOGIN_URL.replace('/login.php', '/dashboard.php')
            r3 = session.get(dashboard_url, timeout=10, verify=False)
            log(f"    Status: {r3.status_code}", f)
            log(f"    Response length: {len(r3.text)}", f)

            if 'access denied' in r3.text.lower()[:500]:
                log(f"    ❌ ACCESS DENIED", f)
                results.append(('FAIL', 'Access denied'))
            elif 'login' in r3.text.lower()[:500] and 'dashboard' not in r3.text.lower()[:500]:
                log(f"    ❌ REDIRECTED TO LOGIN", f)
                results.append(('FAIL', 'Redirected to login'))
            else:
                log(f"    ✓ SUCCESS - Dashboard accessible!", f)
                results.append(('SUCCESS', f'{session_cookie_name} cookie works'))

        except Exception as e:
            log(f"\n❌ EXCEPTION: {e}", f)
            import traceback
            log(traceback.format_exc(), f)
            results.append(('FAIL', str(e)))

        if iteration < 10:
            time.sleep(0.5)

    # Summary
    log(f"\n\n{'='*80}", f)
    log("SUMMARY", f)
    log(f"{'='*80}", f)
    successful = [r for r in results if r[0] == 'SUCCESS']
    failed = [r for r in results if r[0] == 'FAIL']

    log(f"\nSuccessful: {len(successful)}/10", f)
    log(f"Failed: {len(failed)}/10", f)

    if successful:
        log(f"\n✅ At least {len(successful)} login(s) succeeded!", f)
    else:
        log(f"\n❌ All logins failed", f)

print(f"\n✓ Test complete! Results saved to: {OUTPUT_FILE}")
print(f"  Run: Get-Content {OUTPUT_FILE}")

