"""Check if the page served to anonymous (non-logged-in) users has the changes."""
import requests, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"

# Fetch WITHOUT auth (simulating anonymous visitor)
url = f"{BASE}/?nocache={int(time.time())}"
r = requests.get(url, timeout=30, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
})

html = r.text
print(f"Status: {r.status_code}")
print(f"HTML length: {len(html)}")

checks = [
    'background:red',
    'border:5px solid yellow',
    'max-width:700px',
    'platform-features',
]

for pattern in checks:
    found = pattern in html
    print(f"  {'FOUND' if found else 'NOT FOUND'}: {pattern}")

# Check cache headers
for h in ['x-hcdn-cache-status', 'x-cache', 'cf-cache-status', 'age', 'x-hcdn-upstream-rt']:
    if h in r.headers:
        print(f"  Header {h}: {r.headers[h]}")

# Now try with a completely fresh session and different UA
print("\n--- Second request (different UA, no cookies) ---")
session = requests.Session()
r2 = session.get(f"{BASE}/?t={int(time.time())+1}", timeout=30, headers={
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
    'Accept': 'text/html',
})
html2 = r2.text
print(f"Status: {r2.status_code}, Length: {len(html2)}")
for pattern in checks:
    found = pattern in html2
    print(f"  {'FOUND' if found else 'NOT FOUND'}: {pattern}")
for h in ['x-hcdn-cache-status', 'x-cache', 'age']:
    if h in r2.headers:
        print(f"  Header {h}: {r2.headers[h]}")
