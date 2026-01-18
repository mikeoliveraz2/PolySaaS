#!/usr/bin/env python
"""
Test: Are the tokens from the SAME SESSION or different sessions?
"""

import os
import sys
import django
import requests
from bs4 import BeautifulSoup

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, '/c/Users/PC/OneDrive/Documents/GitHub/DoseV3MasterSaaS-main-main')
django.setup()

ODOO_LOGIN = "https://polysaas.odoo.com/odoo/web/login"
DJANGO_PROXY = "http://127.0.0.1:8000/pt/admin/odoo/web/login"

print("="*120)
print("TEST: Single session - fetch form, extract token, post it back")
print("="*120)

# Use SINGLE session for both requests
session = requests.Session()

print("\n1. GET form from ODOO...")
resp1 = session.get(ODOO_LOGIN, timeout=10)
print(f"   Status: {resp1.status_code}")
print(f"   Cookies in session: {len(session.cookies)}")

# Extract token
soup1 = BeautifulSoup(resp1.text, 'html.parser')
form1 = soup1.find('form')
csrf_1 = form1.find('input', {'name': 'csrf_token'}).get('value')
print(f"   CSRF Token: {csrf_1[:50]}...")

print("\n2. POST back to ODOO using same token from same session...")
post_data = {
    'login': 'mikeoliveraz@gmail.com',
    'password': 'M@ster889688p',
    'csrf_token': csrf_1,
    'type': 'password',
    'redirect': '/odoo/web/login?'
}

print(f"   POST data keys: {list(post_data.keys())}")
print(f"   CSRF token in POST: {csrf_1[:50]}...")
print(f"   Content-Type will be: application/x-www-form-urlencoded")

resp2 = session.post(ODOO_LOGIN, data=post_data, timeout=10, allow_redirects=False)
print(f"   Response status: {resp2.status_code}")
print(f"   Response reason: {resp2.reason}")

if resp2.status_code == 303:
    print(f"   ✓ Got redirect (303) - login likely successful!")
    print(f"   Redirect location: {resp2.headers.get('location', 'NONE')}")
elif resp2.status_code == 400:
    print(f"   ✗ Got 400 Bad Request - CSRF token issue?")
    print(f"   Response (first 500 chars): {resp2.text[:500]}")
elif resp2.status_code == 422:
    print(f"   ✗ Got 422 Unprocessable Entity")
    print(f"   Response (first 500 chars): {resp2.text[:500]}")
else:
    print(f"   ? Unexpected status: {resp2.status_code}")
    print(f"   Response (first 500 chars): {resp2.text[:500]}")

print("\n" + "="*120)
print("NOW TEST: Through Django proxy with SAME single session")
print("="*120)

session2 = requests.Session()

print("\n1. GET form from DJANGO PROXY...")
resp3 = session2.get(DJANGO_PROXY, timeout=10)
print(f"   Status: {resp3.status_code}")
print(f"   Cookies in session: {len(session2.cookies)}")

# Extract token from proxy response
soup3 = BeautifulSoup(resp3.text, 'html.parser')
form3 = soup3.find('form')
csrf_3 = form3.find('input', {'name': 'csrf_token'}).get('value')
print(f"   CSRF Token: {csrf_3[:50]}...")

print("\n2. POST back to DJANGO PROXY...")
post_data2 = {
    'login': 'mikeoliveraz@gmail.com',
    'password': 'M@ster889688p',
    'csrf_token': csrf_3,  # Use token from proxy form!
    'type': 'password',
    'redirect': '/odoo/web/login?'
}

print(f"   POST to: {DJANGO_PROXY}")
print(f"   POST data keys: {list(post_data2.keys())}")
print(f"   CSRF token in POST: {csrf_3[:50]}...")

resp4 = session2.post(DJANGO_PROXY, data=post_data2, timeout=10, allow_redirects=False)
print(f"   Response status: {resp4.status_code}")
print(f"   Response reason: {resp4.reason}")

if resp4.status_code == 303:
    print(f"   ✓ Got redirect (303) - login likely successful!")
    print(f"   Redirect location: {resp4.headers.get('location', 'NONE')}")
elif resp4.status_code == 400:
    print(f"   ✗ Got 400 Bad Request - CSRF token issue?")
    print(f"   Response headers: {dict(resp4.headers)}")
    print(f"   Response (first 1000 chars): {resp4.text[:1000]}")
elif resp4.status_code == 422:
    print(f"   ✗ Got 422 Unprocessable Entity")
    print(f"   Response (first 1000 chars): {resp4.text[:1000]}")
else:
    print(f"   ? Unexpected status: {resp4.status_code}")
    print(f"   Response (first 1000 chars): {resp4.text[:1000]}")

print("\n" + "="*120)
