#!/usr/bin/env python
"""
Test the complete Odoo login flow through Django proxy.
Simulates what a browser does:
1. GET /pt/admin/odoo/web/login - get the form with CSRF token
2. Extract the CSRF token
3. POST /pt/admin/odoo/web/login - submit the form
4. Check if we get redirected (login success) or error (login failed)
"""

import requests
from bs4 import BeautifulSoup
import sys

# Disable SSL warnings for self-signed certs
requests.packages.urllib3.disable_warnings()

# Create a session to maintain cookies across requests
session = requests.Session()
session.verify = False

BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/pt/admin/odoo/web/login"

print("="*100)
print("[TEST FLOW] Odoo Login Through Django Proxy")
print("="*100)

# Step 1: GET the login form
print("\n[STEP 1] Fetching login form...")
print(f"URL: {LOGIN_URL}")

try:
    response = session.get(LOGIN_URL, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'NOT SET')}")
    print(f"Content Length: {len(response.content)} bytes")

    if response.status_code != 200:
        print(f"ERROR: Expected 200, got {response.status_code}")
        print(f"Response text (first 500 chars): {response.text[:500]}")
        sys.exit(1)

    # Parse the form
    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form')

    if not form:
        print("ERROR: No form found in response!")
        print(f"Response (first 1000 chars): {response.text[:1000]}")
        sys.exit(1)

    print(f"✓ Form found")
    print(f"  Form action: {form.get('action', 'NOT SET')}")
    print(f"  Form method: {form.get('method', 'NOT SET')}")

    # Extract CSRF token
    csrf_input = form.find('input', {'name': 'csrf_token'})
    if not csrf_input:
        print("ERROR: CSRF token not found in form!")
        print(f"Form inputs: {[inp.get('name') for inp in form.find_all('input')]}")
        sys.exit(1)

    csrf_token = csrf_input.get('value', '')
    print(f"✓ CSRF token extracted: {csrf_token[:50]}...")

    # Extract other form fields
    login_field = form.find('input', {'name': 'login'})
    password_field = form.find('input', {'name': 'password'})

    print(f"✓ Form fields found:")
    print(f"  - login: {login_field is not None}")
    print(f"  - password: {password_field is not None}")
    print(f"  - csrf_token: {csrf_input is not None}")

except requests.exceptions.RequestException as e:
    print(f"ERROR: Failed to fetch login form: {e}")
    sys.exit(1)

# Step 2: POST the login form
print("\n[STEP 2] Submitting login form...")
print(f"URL: {LOGIN_URL}")

login_data = {
    'login': 'mikeoliveraz@gmail.com',
    'password': 'M@ster889688p',
    'csrf_token': csrf_token,
    'redirect': '/',
}

print(f"POST data:")
for key, value in login_data.items():
    if key == 'csrf_token':
        print(f"  {key}: {value[:50]}...")
    else:
        print(f"  {key}: {value}")

try:
    print("\nSending POST request...")
    response = session.post(LOGIN_URL, data=login_data, timeout=10, allow_redirects=False)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'NOT SET')}")
    print(f"Location header: {response.headers.get('location', 'NOT SET')}")
    print(f"Content Length: {len(response.content)} bytes")

    # Check for common responses
    if response.status_code == 200:
        print("\n[RESULT] Got 200 - Checking for error message...")
        if 'session expired' in response.text.lower() or 'csrf' in response.text.lower():
            print("✗ CSRF/Session error in response")
            # Find the error
            soup = BeautifulSoup(response.text, 'html.parser')
            errors = soup.find_all(class_=['alert', 'error', 'notification'])
            for error in errors:
                print(f"  Error: {error.get_text()[:100]}")
        else:
            print("✓ Login form returned (likely form re-rendered)")
    elif response.status_code in [301, 302, 303, 307]:
        print(f"\n[RESULT] ✓ Redirect to: {response.headers.get('location', 'UNKNOWN')}")
        print("✓ LOGIN SUCCESSFUL!")
    else:
        print(f"\n[RESULT] Unexpected status: {response.status_code}")
        print(f"Response (first 500 chars): {response.text[:500]}")

except requests.exceptions.RequestException as e:
    print(f"ERROR: Failed to submit login form: {e}")
    sys.exit(1)

print("\n" + "="*100)
print("[TEST FLOW] Complete")
print("="*100)
