#!/usr/bin/env python
"""Diagnostic script to test Flask proxy connectivity."""

import requests
import sys

PROXY_URL = "http://127.0.0.1:8001/admin/osticket/login.php"

print("=" * 60)
print("FLASK PROXY DIAGNOSTIC TEST")
print("=" * 60)

# Test 1: Check if Flask proxy is running
print(f"\n1. Checking if Flask proxy is running at {PROXY_URL}...")
try:
    response = requests.get(PROXY_URL, timeout=5)
    print(f"   ✓ Flask proxy is running!")
    print(f"   Status Code: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
    print(f"   Content Length: {len(response.text)} bytes")

    # Check for HTML content
    if "<!DOCTYPE" in response.text or "<html" in response.text.lower():
        print("   ✓ Received HTML content")
    else:
        print("   ⚠ Warning: Response doesn't look like HTML")
        print(f"   First 200 chars: {response.text[:200]}")

except requests.exceptions.ConnectionError as e:
    print(f"   ✗ FAILED: Cannot connect to Flask proxy")
    print(f"   Error: {e}")
    print("\n   Make sure to start the Flask proxy with:")
    print("   python -m dose.osticket")
    sys.exit(1)
except requests.exceptions.Timeout:
    print(f"   ✗ FAILED: Flask proxy timeout")
    sys.exit(1)

# Test 2: Check if proxy is rewriting URLs
print(f"\n2. Checking if Flask proxy is rewriting URLs...")
if "/admin/osticket/" in response.text:
    print("   ✓ Found proxy path rewriting in response")
else:
    print("   ⚠ Warning: Proxy path rewriting may not be working")

# Test 3: Check real server connectivity
print(f"\n3. Checking connection to real OSTicket server...")
REAL_URL = "https://oliverenterprises.app.saasify.cloud/scp/login.php"
try:
    real_response = requests.get(REAL_URL, timeout=5, verify=False)
    print(f"   ✓ Real OSTicket server is reachable")
    print(f"   Status Code: {real_response.status_code}")
except Exception as e:
    print(f"   ✗ Cannot reach real OSTicket server")
    print(f"   Error: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
