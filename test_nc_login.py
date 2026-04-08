#!/usr/bin/env python
"""Test Nextcloud login flow directly to upstream."""
import re
import requests

session = requests.Session()

# Step 1: Get fresh login page
print("=== Step 1: Fresh login page ===")
r1 = session.get("http://127.0.0.1:8888/login", allow_redirects=False, timeout=10)
print(f"Status: {r1.status_code}")
print(f"Cookies: {dict(session.cookies)}")

token_match = re.search(r'data-requesttoken="([^"]+)"', r1.text)
requesttoken = token_match.group(1) if token_match else "MISSING"
print(f"Requesttoken: {requesttoken[:50]}...")

# Step 2: POST login
print()
print("=== Step 2: POST login ===")
r2 = session.post(
    "http://127.0.0.1:8888/login",
    data={
        "user": "admin",
        "password": "admin",
        "timezone": "Asia/Singapore",
        "timezone_offset": "8",
        "requesttoken": requesttoken,
    },
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "http://127.0.0.1:8888/login",
    },
    allow_redirects=False,
    timeout=10,
)
print(f"Status: {r2.status_code}")
print(f"Location: {r2.headers.get('Location', 'NONE')}")
print(f"Cookies after POST: {dict(session.cookies)}")

# Step 3: Follow the redirect
if r2.status_code in (301, 302, 303, 307):
    loc = r2.headers.get("Location", "")
    print()
    print(f"=== Step 3: Follow redirect to {loc} ===")
    r3 = session.get(loc if loc.startswith("http") else f"http://127.0.0.1:8888{loc}", 
                     allow_redirects=False, timeout=10)
    print(f"Status: {r3.status_code}")
    if r3.status_code in (301, 302, 303, 307):
        print(f"Location: {r3.headers.get('Location', 'NONE')}")
