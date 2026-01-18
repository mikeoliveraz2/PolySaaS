#!/usr/bin/env python
"""
Quick diagnostic script to test OSTicket proxy form submission
"""
import requests
import re
from bs4 import BeautifulSoup

# Test 1: Load the OSTicket login page
print("=" * 60)
print("TEST 1: Loading OSTicket login page through proxy")
print("=" * 60)

try:
    response = requests.get('http://localhost:8000/admin/osticket/', verify=False)
    print(f"✓ Response status: {response.status_code}")
    print(f"✓ Response length: {len(response.text)} bytes")
    print(f"✓ Content-Type: {response.headers.get('content-type', 'unknown')}")

    # Check for login form
    soup = BeautifulSoup(response.text, 'html.parser')
    forms = soup.find_all('form')
    print(f"✓ Found {len(forms)} form(s)")

    for i, form in enumerate(forms):
        print(f"\n  Form {i+1}:")
        print(f"    ID: {form.get('id', 'N/A')}")
        print(f"    Action: {form.get('action', 'N/A')}")
        print(f"    Method: {form.get('method', 'N/A')}")
        print(f"    OnSubmit: {form.get('onsubmit', 'N/A')[:100]}...")

        # Check for proxy fix script
        if '[OSTicket Proxy]' in response.text:
            print(f"    ✓ Proxy fix script found in page")
        else:
            print(f"    ✗ Proxy fix script NOT found in page")

    # Check for input fields
    inputs = soup.find_all('input')
    print(f"\n✓ Found {len(inputs)} input field(s)")
    for inp in inputs[:5]:  # Show first 5
        print(f"  - {inp.get('name', 'unknown')}: type={inp.get('type', 'text')}")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("TEST 2: Checking form action path")
print("=" * 60)

try:
    response = requests.get('http://localhost:8000/admin/osticket/', verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form')

    if form:
        action = form.get('action', '')
        print(f"Form action: {action}")

        if '/admin/osticket/' in action:
            print(f"✓ Form action correctly points to proxy path")
        else:
            print(f"✗ Form action does NOT point to proxy path")
            print(f"  Expected to contain: /admin/osticket/")
    else:
        print(f"✗ No form found")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("TEST 3: Simulating form submission")
print("=" * 60)

try:
    # First, get the login page to see what form data is expected
    response = requests.get('http://localhost:8000/admin/osticket/', verify=False, allow_redirects=True)
    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form')

    if form:
        action = form.get('action', '')
        method = form.get('method', 'post').lower()

        print(f"Form action: {action}")
        print(f"Form method: {method}")

        # Collect all input fields
        data = {}
        for inp in form.find_all('input'):
            name = inp.get('name')
            value = inp.get('value', '')
            inp_type = inp.get('type', 'text')
            if name:
                data[name] = value
                print(f"  - {name}: {value[:50] if value else '(empty)'}")

        # Try a test submission (won't actually log in, just testing the path)
        data['username'] = 'test'
        data['password'] = 'test'

        print(f"\n  Attempting test submission...")
        if method == 'post':
            if action.startswith('/'):
                url = f"http://localhost:8000{action}"
            else:
                url = action
            print(f"  POST to: {url}")

            resp = requests.post(url, data=data, verify=False, allow_redirects=False)
            print(f"  ✓ Response status: {resp.status_code}")
            print(f"  ✓ Response reason: {resp.reason}")

            # Check if form was actually submitted
            if resp.status_code in [200, 302, 401, 403, 422]:
                print(f"  ✓ Form submission appeared to work (got status {resp.status_code})")
            else:
                print(f"  ? Unexpected response status {resp.status_code}")
    else:
        print(f"✗ No form found on page")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Diagnostic complete")
print("=" * 60)
