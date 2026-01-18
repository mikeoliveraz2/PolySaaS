#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TDD: Test-Driven Development for Odoo Login
Write the test first to define expected behavior, then debug actual behavior
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import sys
import io

# Fix Unicode output for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Suppress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = 'http://127.0.0.1:8000'
ODOO_LOGIN_PATH = '/pt/admin/odoo/web/login'

print("\n" + "=" * 100)
print("TDD TEST: Odoo Login Through Django Proxy")
print("=" * 100)

# Create session that maintains cookies
session = requests.Session()
session.verify = False

# TEST 1: Fetch form
print("\n[TEST 1] Fetch login form - EXPECTED: 200 OK with CSRF token")
print("-" * 100)

form_response = session.get(f"{BASE_URL}{ODOO_LOGIN_PATH}", timeout=10)
assert form_response.status_code == 200, f"FAIL: Got {form_response.status_code}, expected 200"
print(f"[OK] Status 200")

cookies_after_get = dict(session.cookies)
print(f"✓ Cookies after GET: {json.dumps({k: v[:30]+'...' if len(v) > 30 else v for k,v in cookies_after_get.items()})}")

soup = BeautifulSoup(form_response.text, 'html.parser')
form = soup.find('form')
assert form, "FAIL: No form found"
print(f"✓ Form found with action: {form.get('action')}")

inputs = {}
for inp in form.find_all('input'):
    inputs[inp.get('name')] = inp.get('value', '')

assert 'csrf_token' in inputs, "FAIL: No csrf_token in form"
csrf_token_from_get = inputs['csrf_token']
print(f"✓ CSRF token from GET: {csrf_token_from_get[:40]}...")

# TEST 2: Check cookies before POST
print("\n[TEST 2] Verify cookies are preserved before POST")
print("-" * 100)

cookies_before_post = dict(session.cookies)
print(f"Cookies before POST:")
for name, value in cookies_before_post.items():
    print(f"  {name}: {value[:50]}...")

# TEST 3: Submit form
print("\n[TEST 3] Submit login form - EXPECTED: 302/redirect or 200 with dashboard")
print("-" * 100)

login_data = {
    'login': 'mikeoliveraz@gmail.com',
    'password': 'M@ster889688p',
    'csrf_token': csrf_token_from_get,
    'redirect': '/'
}

print(f"Submitting POST with:")
print(f"  csrf_token: {login_data['csrf_token'][:40]}...")
print(f"  login: {login_data['login']}")
print(f"  password: {'*' * len(login_data['password'])}")

login_response = session.post(
    f"{BASE_URL}{ODOO_LOGIN_PATH}",
    data=login_data,
    timeout=10,
    allow_redirects=False  # See actual response
)

print(f"\nResponse Status: {login_response.status_code}")
print(f"Response Content-Type: {login_response.headers.get('content-type', 'NOT SET')}")
print(f"Response Content-Length: {len(login_response.text)} chars")

# Check for redirect
if login_response.status_code in [301, 302, 303, 307, 308]:
    print(f"✓ Got redirect: {login_response.status_code} -> {login_response.headers.get('Location')}")
    result = "SUCCESS"
else:
    # Check for CSRF error
    if 'CSRF' in login_response.text or 'csrf' in login_response.text.lower():
        print(f"✗ CSRF error in response")
        # Extract the error
        if 'invalid CSRF token' in login_response.text:
            print(f"  Error: Session expired (invalid CSRF token)")
            result = "CSRF_ERROR"
        else:
            print(f"  Error: {login_response.text[:200]}")
            result = "CSRF_ERROR"
    else:
        print(f"✓ Got 200, checking if form re-rendered or error...")
        result = "CHECK_RESPONSE"

# TEST 4: Debug - Check response headers for clues
print("\n[TEST 4] DEBUG: Response Headers from Odoo (via middleware)")
print("-" * 100)

print("Response headers:")
for header_name, header_value in login_response.headers.items():
    if len(str(header_value)) > 80:
        print(f"  {header_name}: {str(header_value)[:80]}...")
    else:
        print(f"  {header_name}: {header_value}")

# Check for Set-Cookie
set_cookies = [v for k, v in login_response.headers.items() if k.lower() == 'set-cookie']
print(f"\nSet-Cookie headers: {len(set_cookies)}")
for cookie in set_cookies:
    print(f"  {cookie}")

# TEST 5: Check for security/session headers Odoo might use
print("\n[TEST 5] DEBUG: Session/Security Indicators")
print("-" * 100)

print(f"Session cookies after POST: {len(dict(session.cookies))}")
for name, value in dict(session.cookies).items():
    print(f"  {name}: {value[:50]}...")

# TEST 6: Show the actual response content
print("\n[TEST 6] Response Content (first 2500 chars)")
print("-" * 100)

response_text = login_response.text[:2500]
print(response_text)

# TEST 7: Save full HTML for analysis
print("\n[TEST 7] Saving full response to file for analysis")
print("-" * 100)

with open('odoo_response_full.html', 'w', encoding='utf-8') as f:
    f.write(login_response.text)
print(f"✓ Saved full response ({len(login_response.text)} chars) to odoo_response_full.html")

# Extract form details
soup_full = BeautifulSoup(login_response.text, 'html.parser')
form_full = soup_full.find('form')
if form_full:
    print(f"\nForm analysis:")
    print(f"  action: {form_full.get('action', 'NOT SET')}")
    print(f"  method: {form_full.get('method', 'NOT SET')}")
    print(f"  onsubmit: {form_full.get('onsubmit', 'NOT SET')[:200] if form_full.get('onsubmit') else 'NOT SET'}")

    # Extract all form inputs
    print(f"\n  Form inputs:")
    for inp in form_full.find_all('input'):
        name = inp.get('name', 'UNNAMED')
        inp_type = inp.get('type', 'text')
        value = inp.get('value', '')[:50] if inp.get('value') else '(empty)'
        print(f"    - {name} ({inp_type}): {value}")

# TEST 8: Look for specific Odoo response patterns
print("\n[TEST 8] Pattern Analysis")
print("-" * 100)

if 'odoo.define' in login_response.text:
    print("✓ Response contains odoo.define (Odoo JavaScript)")
if 'login-form' in login_response.text.lower():
    print("✗ Response contains login-form (form still present)")
if 'web/layout' in login_response.text:
    print("✓ Response contains web/layout (dashboard template)")
if '"uid": null' in login_response.text:
    print("✗ Session info shows uid:null (unauthenticated user)")
if 'session' in login_response.text.lower():
    print("✓ Response contains 'session' keyword")
if 'error' in login_response.text.lower():
    print("✗ Response contains error keyword")
    # Find error lines
    for i, line in enumerate(login_response.text.split('\n')):
        if 'error' in line.lower():
            print(f"  Line {i}: {line[:100]}")

print("\n" + "=" * 100)
print(f"TEST RESULT: {result}")
print("=" * 100)

if result == "SUCCESS":
    print("✓ Login successful!")
elif result == "CSRF_ERROR":
    print("✗ CSRF token validation failed")
    print("\nDEBUG INFO:")
    print(f"  Cookies maintained: {len(cookies_after_get) > 0}")
    print(f"  CSRF token from form: {csrf_token_from_get[:40]}...")
    print(f"  CSRF token in POST: {login_data['csrf_token'][:40]}...")
    print(f"  Tokens match: {csrf_token_from_get == login_data['csrf_token']}")
    print("\nNEXT STEPS:")
    print("  1. Check middleware debug log (odoo_post_debug.txt)")
    print("  2. Verify cookie/session preserved through proxy")
    print("  3. Check if Content-Type is form-urlencoded")
    print("  4. Verify CSRF token sent in POST body")
else:
    print("? Unexpected response - check content above")
