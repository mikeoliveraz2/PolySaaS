#!/usr/bin/env python
"""Test POST to Nextcloud login via PolySaaS proxy."""
import re
import requests

POLYSAAS = "http://127.0.0.1:8000"
NC_DIRECT = "http://127.0.0.1:8888"
PROXY_PREFIX = "/pt/admin/nextcloud"

# First get a fresh session + requesttoken directly from Nextcloud
print("=== Step 1: Get fresh session from Nextcloud ===")
nc_session = requests.Session()
r1 = nc_session.get(f"{NC_DIRECT}/login", allow_redirects=False, timeout=10)
print(f"GET {NC_DIRECT}/login -> {r1.status_code}")
print(f"Cookies: {list(nc_session.cookies.keys())}")

token_match = re.search(r'data-requesttoken="([^"]+)"', r1.text)
if not token_match:
    print("ERROR: No requesttoken!")
    exit(1)
requesttoken = token_match.group(1)
print(f"Requesttoken: {requesttoken[:40]}...")

# Now POST via PolySaaS proxy, using the NC session cookies
print("\n=== Step 2: POST login via PolySaaS proxy ===")
# Build cookie header from NC session
cookie_str = "; ".join([f"{k}={v}" for k, v in nc_session.cookies.items()])
# Add PolySaaS Django session (you need to replace these with real values)
cookie_str += "; sessionid=gcpwgwpmftqy8s75b1y8hi3f0vpu1osf; csrftoken=uZEtFLa2VBBUXmwOMh97nnw5KdEvJL9t"

r2 = requests.post(
    f"{POLYSAAS}{PROXY_PREFIX}/login",
    data={
        "user": "admin",
        "password": "admin",
        "timezone": "Asia/Singapore",
        "timezone_offset": "8",
        "requesttoken": requesttoken,
    },
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": f"{POLYSAAS}{PROXY_PREFIX}/login",
        "Cookie": cookie_str,
    },
    allow_redirects=False,
    timeout=10,
)
print(f"POST -> {r2.status_code}")
print(f"Location: {r2.headers.get('Location', 'NONE')}")
print(f"Response cookies: {dict(r2.cookies)}")

if r2.status_code in (301, 302, 303, 307):
    loc = r2.headers.get("Location", "")
    print(f"\n=== Step 3: Following redirect to {loc} ===")
