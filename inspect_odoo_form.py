#!/usr/bin/env python
"""
Inspect Odoo login form to understand required fields and parameters.
"""

import requests
import re

ODOO_BASE = "https://polysaas.odoo.com/odoo"
LOGIN_URL = f"{ODOO_BASE}/web/login"

print(f"\n{'='*80}")
print(f"ODOO LOGIN FORM INSPECTOR")
print(f"{'='*80}\n")

session = requests.Session()
response = session.get(LOGIN_URL)

# Extract form content
form_match = re.search(r'<form[^>]*>.*?</form>', response.text, re.DOTALL)
if form_match:
    form_content = form_match.group(0)
    print("Found form:")
    print(form_content[:1000])
    print("\n" + "="*80 + "\n")

# Extract all input fields
inputs = re.findall(r'<input[^>]*>', response.text)
print("Input fields found:")
for inp in inputs:
    print(f"  {inp}")

print("\n" + "="*80 + "\n")

# Extract all hidden fields specifically
hidden_inputs = re.findall(r'<input[^>]*type=["\']?hidden["\']?[^>]*>', response.text)
print("Hidden inputs:")
for inp in hidden_inputs:
    # Extract name and value
    name_match = re.search(r'name=["\']([^"\']+)["\']', inp)
    value_match = re.search(r'value=["\']([^"\']+)["\']', inp)
    name = name_match.group(1) if name_match else "N/A"
    value = value_match.group(1) if value_match else "N/A"
    print(f"  {name}: {value}")

print("\n" + "="*80 + "\n")

# Check for any data attributes or JSON in the page
script_matches = re.findall(r'<script[^>]*>.*?</script>', response.text, re.DOTALL)
print(f"Found {len(script_matches)} script tags")

# Look for login-related content
if 'csrf_token' in response.text:
    csrf_val = re.search(r'csrf_token["\']?\s*:\s*["\']([^"\']+)["\']', response.text)
    if csrf_val:
        print(f"CSRF Token: {csrf_val.group(1)}")

# Look for user_agent or platform info
if 'webauthn' in response.text:
    print("WebAuthn fields detected - Odoo may support passwordless login")

print(f"\n{'='*80}\n")
