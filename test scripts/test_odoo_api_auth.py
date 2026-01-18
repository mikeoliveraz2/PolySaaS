#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Odoo API Authentication
Try to use the /odoo/api/auth/login endpoint
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
print("TEST: Odoo API Authentication (/odoo/api/auth/login)")
print("=" * 100)

session = requests.Session()
session.verify = False

# Test 1: Try API endpoint with JSON
print("\n[TEST 1] POST to /odoo/api/auth/login with JSON")
print("-" * 100)

auth_data = {
    'login': LOGIN,
    'password': PASSWORD,
}

try:
    response = session.post(
        f'{BASE_URL}/odoo/api/auth/login',
        json=auth_data,
        allow_redirects=False,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Response body: {response.text[:500]}")
    print(f"Cookies: {dict(session.cookies)}")

    if response.status_code == 200:
        try:
            data = response.json()
            print(f"\nJSON Response: {json.dumps(data, indent=2)}")
        except:
            print(f"Not JSON response")

except Exception as e:
    print(f"Error: {e}")

# Test 2: Try with form data
print("\n[TEST 2] POST to /odoo/api/auth/login with form data")
print("-" * 100)

try:
    response = session.post(
        f'{BASE_URL}/odoo/api/auth/login',
        data=auth_data,
        allow_redirects=False,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response body: {response.text[:500]}")
    print(f"Cookies: {dict(session.cookies)}")

except Exception as e:
    print(f"Error: {e}")

# Test 3: Check if we're now authenticated
print("\n[TEST 3] Check authentication status")
print("-" * 100)

try:
    response = session.get(f'{BASE_URL}/web', timeout=10)
    print(f"GET /web: {response.status_code}")

    import re
    if '"uid": null' in response.text:
        print("Still unauthenticated (uid: null)")
    else:
        match = re.search(r'"uid": (\d+)', response.text)
        if match:
            uid = match.group(1)
            print(f"AUTHENTICATED! uid: {uid}")
        else:
            print("Checking response for auth info...")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 100)
