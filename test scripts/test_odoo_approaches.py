#!/usr/bin/env python3
"""
Check if the issue is account/credentials vs cookie handling.
Try multiple approaches to login.
"""
import requests
from bs4 import BeautifulSoup

ODOO_URL = "https://polysaas.odoo.com"
EMAIL = "mikeoliveraz@gmail.com"
PASSWORD = "M@ster889688p"

print("[TEST] Checking Odoo SaaS root and login scenarios\n")

session = requests.Session()

# Approach 1: Check if we can access /odoo/ directly
print("[APPROACH 1] Check /odoo/ main page")
try:
    r = session.get(f"{ODOO_URL}/odoo/", timeout=10)
    print(f"  Status: {r.status_code}")
    print(f"  URL: {r.url}")
    print(f"  Type: {r.headers.get('Content-Type')}")
    print(f"  Length: {len(r.text)} bytes")

    if 'login' in r.text.lower() or 'authenticate' in r.text.lower():
        print(f"  -> Redirected to login page")
    elif 'dashboard' in r.text.lower():
        print(f"  -> Appears to be dashboard (already logged in?)")
    else:
        print(f"  -> Unknown response")
except Exception as e:
    print(f"  ERROR: {e}")

# Approach 2: Try root URL without /odoo/
print("\n[APPROACH 2] Check root URL (polysaas.odoo.com)")
session2 = requests.Session()
try:
    r = session2.get(ODOO_URL, timeout=10, allow_redirects=True)
    print(f"  Status: {r.status_code}")
    print(f"  Final URL: {r.url}")
    print(f"  Cookies: {dict(session2.cookies)}")
except Exception as e:
    print(f"  ERROR: {e}")

# Approach 3: Try API-based login
print("\n[APPROACH 3] Check if Odoo API endpoint exists")
session3 = requests.Session()
try:
    # Odoo JSON-RPC login
    r = session3.post(
        f"{ODOO_URL}/web/session/authenticate",
        json={
            'jsonrpc': '2.0',
            'params': {
                'login': EMAIL,
                'password': PASSWORD,
            }
        },
        timeout=10
    )
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.text[:200]}")
except Exception as e:
    print(f"  ERROR: {e}")

# Approach 4: Check if there's a /web/login page
print("\n[APPROACH 4] Check /web/login (not /odoo/web/login)")
session4 = requests.Session()
try:
    r = session4.get(f"{ODOO_URL}/web/login", timeout=10)
    print(f"  Status: {r.status_code}")
    print(f"  Final URL: {r.url}")

    # Try to login
    soup = BeautifulSoup(r.text, 'html.parser')
    csrf = soup.find('input', {'name': 'csrf_token'})
    if csrf:
        csrf_val = csrf.get('value')
        print(f"  CSRF found: {csrf_val[:20]}...")

        # Submit login
        r2 = session4.post(
            f"{ODOO_URL}/web/login",
            data={
                'login': EMAIL,
                'password': PASSWORD,
                'csrf_token': csrf_val,
            },
            allow_redirects=False
        )
        print(f"  Login response: {r2.status_code}")
        print(f"  Redirect: {r2.headers.get('Location', 'N/A')}")
        print(f"  Cookies after login: {dict(session4.cookies)}")

        # Try CSS with this session
        r3 = session4.get(f"{ODOO_URL}/web/assets/40e3d83/web.assets_frontend.min.css", timeout=10)
        print(f"  CSS request: {r3.status_code}")
        print(f"  CSS type: {r3.headers.get('Content-Type')}")
        if 'text/css' in r3.headers.get('Content-Type', ''):
            print(f"  ✓ SUCCESS - CSS file loaded!")
        else:
            print(f"  ✗ FAILED - Still getting: {r3.headers.get('Content-Type')}")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()
