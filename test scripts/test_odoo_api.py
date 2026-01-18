#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Odoo API Authentication
Try to authenticate using Odoo's REST API instead of form-based login
"""
import requests
import json
import sys
import io

# Fix Unicode output for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Suppress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = 'https://polysaas.odoo.com'
LOGIN = 'mikeoliveraz@gmail.com'
PASSWORD = 'M@ster889688p'

print("\n" + "=" * 100)
print("TEST: Odoo API Authentication Endpoints")
print("=" * 100)

session = requests.Session()
session.verify = False

# Test 1: Check if there's an API endpoint
print("\n[TEST 1] Check for Odoo API endpoints")
print("-" * 100)

api_endpoints = [
    '/api/auth/login',
    '/api/v1/auth/login',
    '/odoo/api/auth/login',
    '/web/session/authenticate',
    '/web/session/login',
]

for endpoint in api_endpoints:
    try:
        url = BASE_URL + endpoint
        response = session.get(url, timeout=5)
        print(f"{endpoint}: {response.status_code}")
    except Exception as e:
        print(f"{endpoint}: ERROR - {str(e)[:50]}")

# Test 2: Try form login but capture what Odoo actually wants
print("\n[TEST 2] Direct POST to /web/login (no form, just data)")
print("-" * 100)

login_data = {
    'login': LOGIN,
    'password': PASSWORD,
}

try:
    response = session.post(
        f'{BASE_URL}/web/login',
        data=login_data,
        allow_redirects=False,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Cookies: {dict(session.cookies)}")

    if response.status_code in [301, 302, 303, 307, 308]:
        print(f"Redirect to: {response.headers.get('Location')}")
    else:
        print(f"Response body length: {len(response.text)}")
        if 'error' in response.text.lower():
            print("ERROR found in response")

except Exception as e:
    print(f"Error: {e}")

# Test 3: Check what Odoo session looks like after any request
print("\n[TEST 3] Check session state after requests")
print("-" * 100)

try:
    response = session.get(f'{BASE_URL}/web', timeout=10)
    print(f"GET /web: {response.status_code}")
    print(f"Session cookies: {dict(session.cookies)}")

    if '"uid": null' in response.text:
        print("Still unauthenticated (uid: null)")
    elif '"uid":' in response.text:
        import re
        match = re.search(r'"uid": (\d+)', response.text)
        if match:
            print(f"Authenticated as uid: {match.group(1)}")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 100)
