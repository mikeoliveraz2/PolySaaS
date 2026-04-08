#!/usr/bin/env python
"""
Comprehensive Nextcloud login flow diagnostics.
Tests both direct upstream and via PolySaaS proxy.
"""
import re
import requests
from urllib.parse import urlencode

# Direct upstream (bypassing PolySaaS)
NC_DIRECT = "http://127.0.0.1:8888"
# Via PolySaaS proxy
POLYSAAS_PROXY = "http://127.0.0.1:8000"
PROXY_PREFIX = "/pt/admin/nextcloud"


def test_direct_login():
    """Test login directly to Nextcloud, bypassing PolySaaS."""
    print("=" * 80)
    print("TEST 1: DIRECT LOGIN TO NEXTCLOUD (bypassing PolySaaS)")
    print("=" * 80)
    
    session = requests.Session()
    
    # Get login page
    r1 = session.get(f"{NC_DIRECT}/login", allow_redirects=False, timeout=10)
    print(f"GET /login -> {r1.status_code}")
    print(f"Session cookies: {list(session.cookies.keys())}")
    
    # Extract requesttoken
    token_match = re.search(r'data-requesttoken="([^"]+)"', r1.text)
    if not token_match:
        print("ERROR: No requesttoken found in HTML!")
        return
    requesttoken = token_match.group(1)
    print(f"Requesttoken: {requesttoken[:40]}...")
    
    # POST login
    r2 = session.post(
        f"{NC_DIRECT}/login",
        data={
            "user": "admin",
            "password": "admin",
            "timezone": "Asia/Singapore",
            "timezone_offset": "8",
            "requesttoken": requesttoken,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        allow_redirects=False,
        timeout=10,
    )
    print(f"POST /login -> {r2.status_code}")
    print(f"Location: {r2.headers.get('Location', 'NONE')}")
    
    if r2.status_code in (301, 302, 303, 307):
        loc = r2.headers.get("Location", "")
        # Follow the redirect
        if loc.startswith("/"):
            # Nextcloud's overwritewebroot makes location = /pt/admin/nextcloud/...
            # So we need to strip that to follow on the direct upstream
            if loc.startswith("/pt/admin/nextcloud"):
                loc = loc[len("/pt/admin/nextcloud"):]
            r3 = session.get(f"{NC_DIRECT}{loc}", allow_redirects=False, timeout=10)
        else:
            r3 = session.get(loc, allow_redirects=False, timeout=10)
        print(f"Following redirect -> {r3.status_code}")
        if r3.status_code in (301, 302, 303, 307):
            print(f"  Another redirect to: {r3.headers.get('Location', 'NONE')}")
        elif r3.status_code == 200:
            if "dashboard" in r3.text.lower() or "files" in r3.text.lower():
                print("  SUCCESS: Reached dashboard/files!")
            elif "login" in r3.text.lower():
                print("  FAILED: Still on login page")
            else:
                print(f"  Reached page, title: {r3.text[:200]}...")


def test_proxy_login():
    """Test login via PolySaaS proxy."""
    print("\n" + "=" * 80)
    print("TEST 2: LOGIN VIA POLYSAAS PROXY")
    print("=" * 80)
    
    session = requests.Session()
    
    # Get login page via proxy
    r1 = session.get(f"{POLYSAAS_PROXY}{PROXY_PREFIX}/login", allow_redirects=False, timeout=10)
    print(f"GET {PROXY_PREFIX}/login -> {r1.status_code}")
    
    if r1.status_code in (301, 302, 303, 307):
        loc = r1.headers.get("Location", "")
        print(f"  Redirected to: {loc}")
        r1 = session.get(f"{POLYSAAS_PROXY}{loc}", allow_redirects=False, timeout=10)
        print(f"  Following -> {r1.status_code}")
    
    print(f"Session cookies: {list(session.cookies.keys())}")
    
    # Check for requesttoken in the HTML
    # Method 1: data-requesttoken attribute on <head>
    token_match = re.search(r'data-requesttoken="([^"]+)"', r1.text)
    # Method 2: script injection (what we do now)
    script_match = re.search(r'document\.head\.dataset\.requesttoken="([^"]+)"', r1.text)
    
    requesttoken = None
    if token_match:
        requesttoken = token_match.group(1)
        print(f"Requesttoken (from data-attr): {requesttoken[:40]}...")
    if script_match:
        requesttoken = script_match.group(1)
        print(f"Requesttoken (from script): {requesttoken[:40]}...")
    
    if not requesttoken:
        print("ERROR: No requesttoken found in proxied HTML!")
        print("HTML preview:")
        print(r1.text[:2000])
        return
    
    # Find the form action
    form_match = re.search(r'<form[^>]*action="([^"]*)"', r1.text, re.IGNORECASE)
    if form_match:
        print(f"Form action: {form_match.group(1)}")
    
    # POST login via proxy
    post_url = f"{POLYSAAS_PROXY}{PROXY_PREFIX}/login"
    print(f"POSTing to: {post_url}")
    
    r2 = session.post(
        post_url,
        data={
            "user": "admin",
            "password": "admin",
            "timezone": "Asia/Singapore",
            "timezone_offset": "8",
            "requesttoken": requesttoken,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{POLYSAAS_PROXY}{PROXY_PREFIX}/login",
        },
        allow_redirects=False,
        timeout=10,
    )
    print(f"POST -> {r2.status_code}")
    print(f"Location: {r2.headers.get('Location', 'NONE')}")
    
    # Check cookies set by the response
    for name, val in r2.cookies.items():
        print(f"  Set-Cookie: {name}={val[:20] if len(val)>20 else val}...")
    
    if r2.status_code in (301, 302, 303, 307):
        loc = r2.headers.get("Location", "")
        if loc.startswith("/"):
            next_url = f"{POLYSAAS_PROXY}{loc}"
        else:
            next_url = loc
        print(f"Following redirect to: {next_url}")
        r3 = session.get(next_url, allow_redirects=False, timeout=10)
        print(f"  -> {r3.status_code}")
        if r3.status_code in (301, 302, 303, 307):
            print(f"  Another redirect to: {r3.headers.get('Location', 'NONE')}")
        elif r3.status_code == 200:
            if "dashboard" in r3.text.lower() or "files" in r3.text.lower():
                print("  SUCCESS: Reached dashboard/files!")
            elif "login" in r3.text.lower():
                print("  FAILED: Still on login page")
                # Check for error messages
                error_match = re.search(r'error["\s>].*?<|"message":\s*"([^"]+)"', r3.text, re.IGNORECASE)
                if error_match:
                    print(f"  Error message: {error_match.group(0)[:200]}")
    elif r2.status_code == 200:
        if "dashboard" in r2.text.lower():
            print("SUCCESS: Logged in directly!")
        elif "login" in r2.text.lower():
            print("FAILED: Still showing login page")
            # Look for error
            if "Temporary error" in r2.text:
                print("  -> 'Temporary error' detected (usually CSRF mismatch)")


def test_cookie_session_match():
    """Test if the session cookie matches the requesttoken."""
    print("\n" + "=" * 80)
    print("TEST 3: SESSION COOKIE vs REQUESTTOKEN CONSISTENCY")
    print("=" * 80)
    
    # Get the login page via proxy
    session = requests.Session()
    r1 = session.get(f"{POLYSAAS_PROXY}{PROXY_PREFIX}/login", allow_redirects=True, timeout=10)
    
    # Get cookies
    print("Cookies after GET /login:")
    for name, val in session.cookies.items():
        print(f"  {name}: {val[:30]}..." if len(val) > 30 else f"  {name}: {val}")
    
    # Get requesttoken
    script_match = re.search(r'document\.head\.dataset\.requesttoken="([^"]+)"', r1.text)
    if script_match:
        print(f"Requesttoken in HTML: {script_match.group(1)[:50]}...")
    else:
        print("ERROR: No requesttoken in HTML!")
        
    # Check if the session cookie (ocr8fneeioe0) is present
    session_cookie = session.cookies.get("ocr8fneeioe0")
    if session_cookie:
        print(f"Session cookie ocr8fneeioe0: {session_cookie[:30]}...")
    else:
        print("WARNING: No ocr8fneeioe0 session cookie!")


if __name__ == "__main__":
    test_direct_login()
    test_proxy_login()
    test_cookie_session_match()
