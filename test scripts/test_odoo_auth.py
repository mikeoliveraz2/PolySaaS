#!/usr/bin/env python3
"""
Test Odoo authentication with provided credentials
"""
import requests
from requests.auth import HTTPBasicAuth
import json
from bs4 import BeautifulSoup

# Credentials
EMAIL = "mikeoliveraz@gmail.com"
PASSWORD = "M@ster889688p"
ODOO_URL = "https://polysaas.odoo.com/odoo"

print(f"[TEST] Testing Odoo authentication")
print(f"[TEST] Email: {EMAIL}")
print(f"[TEST] Password: {'*' * len(PASSWORD)}")
print(f"[TEST] Odoo URL: {ODOO_URL}")
print("=" * 80)

# Create session
session = requests.Session()

try:
    # Step 1: Get login page to extract CSRF token
    print("\n[STEP 1] Fetching login page...")
    login_url = f"{ODOO_URL}/web/login"
    response = session.get(login_url)
    print(f"[RESPONSE] Status: {response.status_code}")
    print(f"[RESPONSE] Content-Type: {response.headers.get('Content-Type')}")
    print(f"[RESPONSE] URL: {response.url}")

    # Parse HTML to find CSRF token
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        csrf_token = csrf_input.get('value')
        print(f"[CSRF] Found token: {csrf_token[:20]}...")
    else:
        print("[CSRF] WARNING: No CSRF token found!")
        csrf_token = None

    # Step 2: Submit login form
    print("\n[STEP 2] Submitting login form...")
    login_data = {
        'login': EMAIL,
        'password': PASSWORD,
        'csrf_token': csrf_token if csrf_token else '',
        'type': 'password',
    }

    print(f"[POST] URL: {login_url}")
    print(f"[POST] Data: {login_data}")

    response = session.post(
        login_url,
        data=login_data,
        allow_redirects=False,  # Don't follow redirects to see the response
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': login_url,
        }
    )

    print(f"[RESPONSE] Status: {response.status_code}")
    print(f"[RESPONSE] Content-Type: {response.headers.get('Content-Type')}")
    print(f"[RESPONSE] Location (redirect): {response.headers.get('Location', 'N/A')}")
    print(f"[RESPONSE] Set-Cookie: {response.headers.get('Set-Cookie', 'N/A')}")
    print(f"[RESPONSE] Content length: {len(response.text)} bytes")

    # Check if login was successful
    if response.status_code in [301, 302, 303, 307]:
        print(f"[LOGIN] ✓ Got redirect response (success indicator)")
        redirect_url = response.headers.get('Location')
        print(f"[LOGIN] Redirect to: {redirect_url}")

        # Check session cookies
        print(f"\n[SESSION] Cookies in session:")
        for name, value in session.cookies.items():
            print(f"  - {name}: {value[:30]}..." if len(value) > 30 else f"  - {name}: {value}")

        # Try to fetch a resource that requires auth
        print("\n[STEP 3] Testing authenticated request to CSS...")
        css_url = f"{ODOO_URL}/web/assets/40e3d83/web.assets_frontend.min.css"
        response = session.get(css_url, allow_redirects=True)
        print(f"[CSS] Status: {response.status_code}")
        print(f"[CSS] Content-Type: {response.headers.get('Content-Type')}")

        if response.status_code == 200:
            if 'text/html' in response.headers.get('Content-Type', ''):
                print(f"[CSS] ✗ FAILED - Still returning HTML (not authenticated)")
                print(f"[CSS] Content preview: {response.text[:200]}")
            elif 'text/css' in response.headers.get('Content-Type', ''):
                print(f"[CSS] ✓ SUCCESS - CSS file returned with correct MIME type")
                print(f"[CSS] Content length: {len(response.text)} bytes")
            else:
                print(f"[CSS] ? Unknown - Got {response.headers.get('Content-Type')}")
        else:
            print(f"[CSS] ✗ FAILED - Status {response.status_code}")

    elif response.status_code == 200:
        print(f"[LOGIN] ✗ Login failed - still on login page (status 200)")
        # Check if form is still present
        if '<form' in response.text.lower() or 'login' in response.text.lower():
            print(f"[LOGIN] Login form still present in response")
            # Try to extract error message
            soup = BeautifulSoup(response.text, 'html.parser')
            error_div = soup.find('div', {'class': 'alert'})
            if error_div:
                print(f"[ERROR] {error_div.get_text(strip=True)}")
    else:
        print(f"[LOGIN] ✗ Unexpected status: {response.status_code}")

    print("\n" + "=" * 80)

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
