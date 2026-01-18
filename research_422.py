#!/usr/bin/env python
"""
Research the 422 error by testing various scenarios
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

print("\n" + "="*80)
print("OSTicket 422 Error Research")
print("="*80 + "\n")

BASE = "https://oliverenterprises.app.saasify.cloud"
SCP = f"{BASE}/scp/"

# Test 1: Just the base URL
print("Test 1: Base URL without /scp/")
print(f"  URL: {BASE}/")
try:
    r = requests.get(f"{BASE}/", timeout=5, verify=False, allow_redirects=True)
    print(f"  Status: {r.status_code}")
    print(f"  Final URL: {r.url}")
    print(f"  Content length: {len(r.text)}")
    if r.status_code != 200:
        print(f"  Response: {r.text[:200]}")
except Exception as e:
    print(f"  Error: {e}")
print()

# Test 2: /scp/ directory
print("Test 2: /scp/ directory (no file)")
print(f"  URL: {SCP}")
try:
    r = requests.get(SCP, timeout=5, verify=False, allow_redirects=True)
    print(f"  Status: {r.status_code}")
    print(f"  Final URL: {r.url}")
    print(f"  Content length: {len(r.text)}")
    if r.status_code != 200:
        print(f"  Response: {r.text[:200]}")
except Exception as e:
    print(f"  Error: {e}")
print()

# Test 3: /scp/login.php (specific file)
print("Test 3: /scp/login.php (specific file)")
print(f"  URL: {SCP}login.php")
try:
    r = requests.get(f"{SCP}login.php", timeout=5, verify=False, allow_redirects=True)
    print(f"  Status: {r.status_code}")
    print(f"  Final URL: {r.url}")
    print(f"  Content length: {len(r.text)}")
    if r.status_code != 200:
        print(f"  Response: {r.text[:200]}")
except Exception as e:
    print(f"  Error: {e}")
print()

# Test 4: /scp/dashboard.php
print("Test 4: /scp/dashboard.php")
print(f"  URL: {SCP}dashboard.php")
try:
    r = requests.get(f"{SCP}dashboard.php", timeout=5, verify=False, allow_redirects=True)
    print(f"  Status: {r.status_code}")
    print(f"  Final URL: {r.url}")
    print(f"  Content length: {len(r.text)}")
    if r.status_code != 200:
        print(f"  Response: {r.text[:200]}")
except Exception as e:
    print(f"  Error: {e}")
print()

# Test 5: With Session (like Flask proxy uses)
print("Test 5: Using Session (Flask proxy approach)")
print(f"  URL: {SCP}login.php")
try:
    sess = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    sess.mount('http://', adapter)
    sess.mount('https://', adapter)

    r = sess.get(f"{SCP}login.php", timeout=5, verify=False, allow_redirects=True)
    print(f"  Status: {r.status_code}")
    print(f"  Final URL: {r.url}")
    print(f"  Content length: {len(r.text)}")
    if r.status_code != 200:
        print(f"  Response: {r.text[:200]}")
except Exception as e:
    print(f"  Error: {e}")
print()

# Test 6: With extra headers
print("Test 6: With browser-like headers")
print(f"  URL: {SCP}login.php")
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    r = requests.get(f"{SCP}login.php", headers=headers, timeout=5, verify=False, allow_redirects=True)
    print(f"  Status: {r.status_code}")
    print(f"  Final URL: {r.url}")
    print(f"  Content length: {len(r.text)}")
    if r.status_code != 200:
        print(f"  Response: {r.text[:200]}")
except Exception as e:
    print(f"  Error: {e}")
print()

print("="*80)
print("Analysis:")
print("  If Test 3-6 all show 422: endpoint is consistently rejecting requests")
print("  If Test 5 shows 200 but Test 1-4 show 422: it's session/cookie related")
print("  If Test 6 shows 200 but others show 422: it's header related")
print("="*80 + "\n")
