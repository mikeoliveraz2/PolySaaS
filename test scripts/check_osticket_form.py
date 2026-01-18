#!/usr/bin/env python
"""
Quick check: Does OSTicket login form have CSRF token?
"""
import requests
from bs4 import BeautifulSoup

# Get the login page
url = "https://oliverenterprises.app.saasify.cloud/scp/login.php"
response = requests.get(url)

print("="*80)
print("OSTicket Login Form Analysis")
print("="*80)
print(f"\nStatus Code: {response.status_code}")
print(f"Cookies received: {list(response.cookies.keys())}")

soup = BeautifulSoup(response.text, 'html.parser')

# Find the login form
forms = soup.find_all('form')
print(f"\nFound {len(forms)} form(s)")

for i, form in enumerate(forms):
    print(f"\n--- Form {i+1} ---")
    print(f"Action: {form.get('action', 'NO ACTION')}")
    print(f"Method: {form.get('method', 'GET')}")

    # Check for CSRF token
    csrf_inputs = form.find_all('input', {'name': lambda x: x and 'csrf' in x.lower()})
    if csrf_inputs:
        for csrf in csrf_inputs:
            print(f"CSRF Token Found: name='{csrf.get('name')}', value='{csrf.get('value', '')[:50]}...'")
    else:
        print("❌ NO CSRF TOKEN FOUND IN FORM!")

    # List all input fields
    inputs = form.find_all('input')
    print(f"\nAll input fields ({len(inputs)}):")
    for inp in inputs:
        name = inp.get('name', 'NO NAME')
        input_type = inp.get('type', 'text')
        value = inp.get('value', '')
        print(f"  - {input_type}: name='{name}', value='{value[:30] if value else 'EMPTY'}...'")

print("\n" + "="*80)
