#!/usr/bin/env python
"""
Test Nextcloud login via PolySaaS proxy.
First logs into Django, then tests Nextcloud passthrough.
"""
import re
import requests

POLYSAAS = "http://127.0.0.1:8000"
PROXY_PREFIX = "/pt/admin/nextcloud"

# Django admin credentials
DJANGO_USER = "olientAdmin"
DJANGO_PASS = "admin"


def get_django_session():
    """Log into Django and return a session with auth cookies."""
    session = requests.Session()
    
    # Get login page to get CSRF token
    r1 = session.get(f"{POLYSAAS}/accounts/login/", timeout=10)
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r1.text)
    if not csrf_match:
        print("ERROR: Could not find Django CSRF token")
        return None
    csrf = csrf_match.group(1)
    
    # Login to Django
    r2 = session.post(
        f"{POLYSAAS}/accounts/login/",
        data={
            "csrfmiddlewaretoken": csrf,
            "login": DJANGO_USER,
            "password": DJANGO_PASS,
        },
        headers={"Referer": f"{POLYSAAS}/accounts/login/"},
        allow_redirects=False,
        timeout=10,
    )
    
    if r2.status_code not in (302, 303):
        print(f"Django login failed: {r2.status_code}")
        return None
    
    # Follow redirect to complete login
    loc = r2.headers.get("Location", "/")
    session.get(f"{POLYSAAS}{loc}" if loc.startswith("/") else loc, timeout=10)
    
    print("Django login successful!")
    print(f"Session cookies: {list(session.cookies.keys())}")
    return session


def test_nextcloud_via_proxy(session):
    """Test Nextcloud login via PolySaaS proxy."""
    print("\n" + "=" * 80)
    print("TEST: NEXTCLOUD LOGIN VIA POLYSAAS PROXY")
    print("=" * 80)
    
    # Get Nextcloud login page via proxy
    url = f"{POLYSAAS}{PROXY_PREFIX}/login"
    print(f"GET {url}")
    r1 = session.get(url, allow_redirects=True, timeout=10)
    print(f"Final URL: {r1.url}")
    print(f"Status: {r1.status_code}")
    print(f"Cookies now: {list(session.cookies.keys())}")
    
    # Check for Nextcloud's requesttoken
    script_match = re.search(r'document\.head\.dataset\.requesttoken="([^"]+)"', r1.text)
    attr_match = re.search(r'data-requesttoken="([^"]+)"', r1.text)
    
    requesttoken = None
    if script_match:
        requesttoken = script_match.group(1)
        print(f"Requesttoken (from script): {requesttoken[:40]}...")
    elif attr_match:
        requesttoken = attr_match.group(1)
        print(f"Requesttoken (from attr): {requesttoken[:40]}...")
    else:
        print("ERROR: No requesttoken found!")
        print("HTML snippet:")
        print(r1.text[:3000])
        return
    
    # Check for form action
    form_match = re.search(r'<form[^>]*action="([^"]*)"', r1.text, re.IGNORECASE)
    if form_match:
        print(f"Form action: {form_match.group(1)}")
    
    # POST login
    print("\n--- POSTing login form ---")
    r2 = session.post(
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
        },
        allow_redirects=False,
        timeout=10,
    )
    print(f"POST status: {r2.status_code}")
    print(f"Location: {r2.headers.get('Location', 'NONE')}")
    
    # Check Set-Cookie
    for name, val in r2.cookies.items():
        print(f"Set-Cookie: {name}")
    
    if r2.status_code in (301, 302, 303, 307):
        loc = r2.headers.get("Location", "")
        print(f"\n--- Following redirect to {loc} ---")
        if loc.startswith("/"):
            next_url = f"{POLYSAAS}{loc}"
        else:
            next_url = loc
        r3 = session.get(next_url, allow_redirects=True, timeout=10)
        print(f"Final URL: {r3.url}")
        print(f"Status: {r3.status_code}")
        
        if "dashboard" in r3.text.lower() or "files" in r3.text.lower():
            print("\nSUCCESS: Reached Nextcloud dashboard/files!")
        elif "login" in r3.text.lower():
            print("\nFAILED: Still on login page")
            if "Temporary error" in r3.text:
                print("  -> 'Temporary error' detected (CSRF mismatch)")
            # Check for other errors
            error_match = re.search(r'class="[^"]*error[^"]*"[^>]*>([^<]+)', r3.text, re.IGNORECASE)
            if error_match:
                print(f"  -> Error message: {error_match.group(1)}")
    elif r2.status_code == 200:
        if "dashboard" in r2.text.lower():
            print("\nSUCCESS: Logged in directly!")
        elif "login" in r2.text.lower():
            print("\nFAILED: Still showing login page")


if __name__ == "__main__":
    session = get_django_session()
    if session:
        test_nextcloud_via_proxy(session)
