#!/usr/bin/env python
"""
Full cycle test: GET login page → Extract CSRF → POST login → Verify success

This simulates the exact flow a browser would take, including session persistence.
"""

import os
import sys
import django
import requests
from bs4 import BeautifulSoup

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from dose.osticket_admin import get_osticket_session

# Configuration
OSTICKET_LOGIN_URL = "https://oliverenterprises.app.saasify.cloud/scp/login.php"
OSTICKET_BASE = "https://oliverenterprises.app.saasify.cloud/scp/"

# Test credentials (use your actual credentials)
TEST_USERNAME = "adminuser"
TEST_PASSWORD = "M@ster889688p"


def test_full_login_cycle():
    """Test the complete login cycle with persistent session."""
    print("="*80)
    print("FULL CYCLE TEST: GET -> Extract CSRF -> POST -> Verify")
    print("="*80)

    # Use the SAME persistent session for both GET and POST
    session = get_osticket_session()

    print("\n[STEP 1] GET login page")
    print("-" * 80)

    # GET request with cache-busting headers
    headers = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    get_response = session.get(
        OSTICKET_LOGIN_URL,
        headers=headers,
        verify=False,
        allow_redirects=False,
        timeout=15
    )

    print(f"Status: {get_response.status_code}")
    print(f"Cookies after GET: {[c.name for c in session.cookies]}")

    if 'OSTSESSID' in session.cookies:
        ostsessid = session.cookies.get('OSTSESSID')
        print(f"OSTSESSID: {ostsessid[:50]}...")

    # Extract CSRF token (check both meta tag and input field)
    soup = BeautifulSoup(get_response.text, 'html.parser')

    csrf_token = None
    # First try meta tag
    meta = soup.find("meta", {"name": "csrf_token"})
    if meta:
        csrf_token = meta.get("content")
        print("[INFO] Found CSRF token in meta tag")

    # Fallback: look for input field
    if not csrf_token:
        form = soup.find('form')
        if form:
            csrf_input = form.find('input', {'name': '__CSRFToken__'})
            if csrf_input:
                csrf_token = csrf_input.get('value', '')
                print("[INFO] Found CSRF token in input field")

    if not csrf_token:
        print("[FAIL] No CSRF token found (checked meta tag and input field)")
        return False

    # Get form action if form exists
    form = soup.find('form')
    form_action = form.get('action', '') if form else ''

    print(f"\n[STEP 2] Extracted form data")
    print("-" * 80)
    print(f"Form action: {form_action}")
    print(f"CSRF token: {csrf_token[:50]}...")
    print(f"CSRF token length: {len(csrf_token)}")

    # Build POST data
    post_data = {
        '__CSRFToken__': csrf_token,
        'userid': TEST_USERNAME,
        'passwd': TEST_PASSWORD,
        'do': 'scplogin',
        'ajax': '1'  # CRITICAL: OSTicket requires this for AJAX login
    }

    print(f"\n[STEP 3] POST login")
    print("-" * 80)
    print(f"POST URL: {OSTICKET_LOGIN_URL}")
    print(f"POST data keys: {list(post_data.keys())}")
    print(f"OSTSESSID being sent: {session.cookies.get('OSTSESSID', 'NOT FOUND')[:50]}...")
    print(f"CSRF token being sent: {csrf_token[:50]}...")

    # POST request with proper AJAX headers
    post_headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': OSTICKET_LOGIN_URL,
        'Origin': 'https://oliverenterprises.app.saasify.cloud',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    post_response = session.post(
        OSTICKET_LOGIN_URL,
        data=post_data,
        headers=post_headers,
        verify=False,
        allow_redirects=False,
        timeout=15
    )

    print(f"\n[STEP 4] POST response")
    print("-" * 80)
    print(f"Status: {post_response.status_code}")
    print(f"Location header: {post_response.headers.get('Location', 'NONE')}")
    print(f"Set-Cookie headers: {post_response.headers.get('Set-Cookie', 'NONE')}")
    print(f"Cookies after POST: {[c.name for c in session.cookies]}")

    # Check for "access denied" in response
    if 'access denied' in post_response.text.lower():
        print("\n[FAIL] Response contains 'access denied'")
        print(f"Response preview: {post_response.text[:500]}...")

        # Compare CSRF token
        if csrf_token in post_response.text:
            print("[INFO] CSRF token found in response (might be showing error page)")
        else:
            print("[WARNING] CSRF token NOT in response")

        return False

    # Check for redirect (success)
    if post_response.status_code in [301, 302, 303, 307]:
        location = post_response.headers.get('Location', '')
        if '/scp/' in location and 'login.php' not in location:
            print("\n[SUCCESS] Login successful! Redirected to dashboard")
            return True
        else:
            print(f"\n[WARNING] Redirected but location looks wrong: {location}")
            return False

    # Check response content
    if 'welcome' in post_response.text.lower() or 'dashboard' in post_response.text.lower():
        print("\n[SUCCESS] Login successful! Dashboard content found")
        return True

    print(f"\n[UNKNOWN] Unexpected response")
    print(f"Response preview: {post_response.text[:500]}...")
    return False


if __name__ == '__main__':
    success = test_full_login_cycle()
    sys.exit(0 if success else 1)

