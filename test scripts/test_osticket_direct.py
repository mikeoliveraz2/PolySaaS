#!/usr/bin/env python
"""
Quick test to verify OSTicket endpoint is reachable and working
"""
import requests
import sys

print("\n" + "="*80)
print("OSTicket Endpoint Direct Test")
print("="*80 + "\n")

ENDPOINT = "https://oliverenterprises.app.saasify.cloud/scp/"
LOGIN_PAGE = ENDPOINT + "login.php"

print(f"Testing: {LOGIN_PAGE}\n")

try:
    # Test with various approaches
    print("1. Simple GET request...")
    r1 = requests.get(LOGIN_PAGE, timeout=5, verify=False)
    print(f"   Status: {r1.status_code}")
    print(f"   Content-Type: {r1.headers.get('content-type', 'unknown')}")
    print(f"   Content Length: {len(r1.text)}")

    # Check what we got
    if r1.status_code == 200:
        print("   ✓ SUCCESS - Got 200 OK")
        if '<' in r1.text[:100]:
            print("   ✓ Response contains HTML")
    elif r1.status_code == 422:
        print("   ❌ Got 422 - Unprocessable Entity")
        print(f"   Response: {r1.text[:200]}")
    else:
        print(f"   Response text: {r1.text[:200]}")

    print("\n2. GET with proper headers...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    r2 = requests.get(LOGIN_PAGE, headers=headers, timeout=5, verify=False)
    print(f"   Status: {r2.status_code}")
    if r2.status_code != r1.status_code:
        print(f"   (Different from simple GET)")

    print("\n3. GET with session...")
    sess = requests.Session()
    r3 = sess.get(LOGIN_PAGE, timeout=5, verify=False)
    print(f"   Status: {r3.status_code}")
    if r3.status_code != r1.status_code:
        print(f"   (Different from simple GET)")

    print("\n" + "="*80)
    print("Summary:")
    print(f"  Endpoint: {LOGIN_PAGE}")
    print(f"  Direct Status: {r1.status_code}")
    if r1.status_code == 200:
        print("  ✓ Endpoint is working! Issue might be with Django view.")
    elif r1.status_code == 422:
        print("  ❌ Endpoint returns 422 - May require specific headers/auth")
    else:
        print(f"  ? Unknown status {r1.status_code}")
    print("="*80 + "\n")

except Exception as e:
    print(f"ERROR: {e}")
    print(f"Type: {type(e).__name__}")
    sys.exit(1)
