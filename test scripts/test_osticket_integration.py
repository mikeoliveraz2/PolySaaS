#!/usr/bin/env python
"""End-to-end test of OSTicket proxy integration."""

import requests
import sys
import time

print("=" * 70)
print("OSTICKET PROXY INTEGRATION TEST")
print("=" * 70)

# Test 1: Flask proxy connectivity
print("\n[Test 1] Checking Flask proxy on port 8001...")
try:
    r = requests.get("http://127.0.0.1:8001/", timeout=3)
    if r.status_code == 200:
        print("  ✓ Flask proxy is running")
    else:
        print(f"  ✗ Unexpected status: {r.status_code}")
except Exception as e:
    print(f"  ✗ Flask proxy not accessible: {e}")
    print("  → Start it with: python -m dose.osticket")
    sys.exit(1)

# Test 2: Proxy route to OSTicket
print("\n[Test 2] Testing proxy route to OSTicket login...")
try:
    r = requests.get("http://127.0.0.1:8001/admin/osticket/login.php", timeout=10)
    print(f"  Status: {r.status_code}")
    print(f"  Content-Type: {r.headers.get('content-type', 'N/A')}")
    print(f"  Content size: {len(r.text)} bytes")

    # Check for proxy path rewriting
    if "/admin/osticket/" in r.text:
        print("  ✓ URL rewriting working (found /admin/osticket/ in content)")
    else:
        print("  ⚠ URL rewriting may not be working")

    # Check for HTML
    if "<!DOCTYPE" in r.text or "<html" in r.text.lower():
        print("  ✓ Received HTML content")
    else:
        print("  ⚠ Warning: Response doesn't look like HTML")

except requests.exceptions.Timeout:
    print("  ✗ Timeout - OSTicket server not responding")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 3: Django backend request
print("\n[Test 3] Simulating Django backend request to proxy...")
try:
    # This is what dose/admin.py does
    proxy_url = "http://127.0.0.1:8001/admin/osticket/login.php"
    r = requests.get(proxy_url, timeout=10)
    print(f"  Status: {r.status_code}")

    if r.status_code == 200:
        print("  ✓ Backend can successfully request proxy")
    else:
        print(f"  ⚠ Unexpected status: {r.status_code}")

except Exception as e:
    print(f"  ✗ Backend request failed: {e}")

# Test 4: Check for path duplication
print("\n[Test 4] Checking for path duplication issues...")
try:
    r = requests.get("http://127.0.0.1:8001/admin/osticket/login.php", timeout=10)

    # Look for bad patterns
    bad_patterns = [
        "/scp/scp/",
        "login.php/login.php",
        "/admin/osticket/admin/osticket/",
    ]

    found_issues = False
    for pattern in bad_patterns:
        if pattern in r.text:
            print(f"  ✗ Found bad pattern: {pattern}")
            found_issues = True

    if not found_issues:
        print("  ✓ No path duplication detected")

except Exception as e:
    print(f"  ⚠ Could not check: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print("\nNext step:")
print("  1. Visit: http://127.0.0.1:8000/admin/osticket/")
print("  2. Should see OSTicket login content inside Django admin")
print("  3. Check browser console for any JavaScript errors")
