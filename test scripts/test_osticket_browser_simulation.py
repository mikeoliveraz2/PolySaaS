"""
Simulate the exact browser flow to debug "access denied" issue.
This simulates what happens when a browser makes GET then POST requests.
"""
import os
import sys
import django
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
django.setup()

from dose.models import PassThroughEndpoint
from dose.osticket_admin import get_osticket_session

# Configuration
OSTICKET_URL = "https://oliverenterprises.app.saasify.cloud/scp/"
LOGIN_URL = f"{OSTICKET_URL}login.php"
USERNAME = "olientAdmin"
PASSWORD = "Dose2025!"

def simulate_browser_flow():
    """
    Simulate browser flow:
    1. GET login page (browser has no cookies initially)
    2. Browser receives cookies from response
    3. POST login (browser sends cookies from step 2)
    """
    print("="*80)
    print("BROWSER FLOW SIMULATION: GET -> Save Cookies -> POST with Cookies")
    print("="*80)

    # Simulate browser cookie storage
    browser_cookies = {}

    # Step 1: GET login page (like browser first visit)
    print("\n[STEP 1] GET login page (browser has no cookies)")
    print("-"*80)
    session = get_osticket_session()

    # Browser has no cookies initially
    print(f"Browser cookies (before GET): {browser_cookies}")
    print(f"Session cookies (before GET): {dict(session.cookies)}")

    # Make GET request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }

    response = session.get(LOGIN_URL, headers=headers, timeout=15, verify=False, allow_redirects=False)
    print(f"GET Status: {response.status_code}")
    print(f"Session cookies (after GET): {dict(session.cookies)}")

    # Browser receives cookies from Set-Cookie headers
    if 'Set-Cookie' in response.headers:
        print(f"Set-Cookie header: {response.headers['Set-Cookie']}")
        # Parse and store in browser
        from http.cookies import SimpleCookie
        cookie = SimpleCookie()
        cookie.load(response.headers['Set-Cookie'])
        for key, morsel in cookie.items():
            browser_cookies[key] = morsel.value
            print(f"Browser saved cookie: {key}={morsel.value[:50]}...")

    # Extract CSRF token from form
    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form')
    csrf_input = form.find('input', {'name': '__CSRFToken__'}) if form else None
    csrf_token = csrf_input.get('value') if csrf_input else None

    print(f"\n[STEP 2] Extracted form data")
    print("-"*80)
    print(f"Form action: {form.get('action', 'NONE') if form else 'NO FORM'}")
    print(f"CSRF token: {csrf_token[:50] if csrf_token else 'NONE'}...")
    print(f"Browser cookies (after GET): {browser_cookies}")

    if not csrf_token:
        print("ERROR: No CSRF token found!")
        return False

    # Step 3: POST login (browser sends cookies from step 2)
    print(f"\n[STEP 3] POST login (browser sends cookies)")
    print("-"*80)

    # CRITICAL: Sync browser cookies to session (like our code does)
    print("Syncing browser cookies to session...")
    for cookie_name in ['OSTSESSID', 'csrf_token']:
        if cookie_name in browser_cookies:
            browser_value = browser_cookies[cookie_name]
            session_value = session.cookies.get(cookie_name)

            print(f"Cookie {cookie_name}:")
            print(f"  Browser: {browser_value[:50] if browser_value else 'NONE'}...")
            print(f"  Session (before): {session_value[:50] if session_value else 'NONE'}...")

            if browser_value and session_value:
                if browser_value != session_value:
                    print(f"  WARNING: Cookies differ! Using SESSION cookie (from GET)")
                    # Keep session cookie
                else:
                    print(f"  Cookies match - using browser cookie")
                    session.cookies.set(cookie_name, browser_value)
            elif browser_value:
                print(f"  Only browser has it - syncing to session")
                session.cookies.set(cookie_name, browser_value)
            elif session_value:
                print(f"  Only session has it - keeping session cookie")
            else:
                print(f"  WARNING: Neither has it!")

    print(f"Session cookies (after sync): {dict(session.cookies)}")

    # Make POST request
    post_data = {
        '__CSRFToken__': csrf_token,
        'userid': USERNAME,
        'passwd': PASSWORD,
        'do': 'scplogin'
    }

    print(f"\nPOST data:")
    print(f"  __CSRFToken__: {csrf_token[:50]}...")
    print(f"  userid: {USERNAME}")
    print(f"  OSTSESSID in session: {session.cookies.get('OSTSESSID', 'NONE')[:50] if session.cookies.get('OSTSESSID') else 'NONE'}...")

    post_response = session.post(
        LOGIN_URL,
        data=post_data,
        headers=headers,
        timeout=15,
        verify=False,
        allow_redirects=False
    )

    print(f"\n[STEP 4] POST response")
    print("-"*80)
    print(f"Status: {post_response.status_code}")
    print(f"Location: {post_response.headers.get('Location', 'NONE')}")
    print(f"Set-Cookie: {post_response.headers.get('Set-Cookie', 'NONE')}")
    print(f"Session cookies (after POST): {dict(session.cookies)}")

    if post_response.status_code in [301, 302, 303, 307]:
        print("\n[SUCCESS] Login successful! Got redirect.")
        return True
    elif 'access denied' in post_response.text.lower():
        print("\n[FAILURE] Access denied in response")
        print(f"Response preview: {post_response.text[:500]}")
        return False
    else:
        print(f"\n[UNKNOWN] Unexpected response")
        print(f"Response preview: {post_response.text[:500]}")
        return False

if __name__ == '__main__':
    success = simulate_browser_flow()
    sys.exit(0 if success else 1)

