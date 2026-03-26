"""Verify what HTML is actually being served to browsers right now."""
import requests, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"

# Fetch with cache-busting query parameter
url = f"{BASE}/?nocache={int(time.time())}"
r = requests.get(url, timeout=30, headers={
    'Cache-Control': 'no-cache, no-store',
    'Pragma': 'no-cache'
})

html = r.text
print(f"Status: {r.status_code}")
print(f"HTML length: {len(html)}")

# Check for our test changes
checks = [
    ('background:red', 'RED BACKGROUND test'),
    ('border:5px solid yellow', 'YELLOW BORDER test'),
    ('max-width:700px', '700px width test'),
    ('max-width:1000px', '1000px width (previous)'),
    ('platform-features', 'Platform Features ID'),
    ('Platform Features', 'Platform Features text'),
]

for pattern, desc in checks:
    found = pattern in html
    print(f"  {'FOUND' if found else 'NOT FOUND'}: {desc} ({pattern})")

# Show the exact HTML around platform-features
pf_pos = html.find('platform-features')
if pf_pos > 0:
    start = max(0, pf_pos - 400)
    end = min(len(html), pf_pos + 100)
    print(f"\n=== HTML around platform-features ===")
    print(html[start:end])

# Check if there might be a different page being served
# Look for the page title
import re
title = re.search(r'<title>(.*?)</title>', html)
if title:
    print(f"\nPage title: {title.group(1)}")

# Check for any CDN/cache headers
print(f"\n=== Response Headers ===")
for h, v in r.headers.items():
    print(f"  {h}: {v}")
