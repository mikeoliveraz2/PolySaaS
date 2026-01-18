#!/usr/bin/env python
"""Direct endpoint test - no Django, just raw requests"""
import requests
from bs4 import BeautifulSoup

url = 'https://oliverenterprises.app.saasify.cloud/scp/'

print(f"\nTesting: {url}\n")

try:
    # Try different endpoints
    endpoints = [
        url,
        url + 'login.php',
        url + 'dashboard.php',
        url.replace('/scp/', '/'),
        url.replace('/scp/', '/admin/'),
    ]

    for ep in endpoints:
        try:
            print(f"\n{'='*60}")
            print(f"Testing: {ep}")
            print('='*60)
            r = requests.get(ep, timeout=5, verify=False, allow_redirects=True)
            print(f"Status: {r.status_code}")
            print(f"Content-Type: {r.headers.get('content-type', 'N/A')}")
            print(f"Content Length: {len(r.text)}")
            print(f"First 300 chars:\n{r.text[:300]}\n")

            # Try to parse HTML
            if '<' in r.text:
                soup = BeautifulSoup(r.text, 'html.parser')
                title = soup.find('title')
                print(f"Title: {title.string if title else 'N/A'}")
        except Exception as e:
            print(f"  Error: {e}")

except Exception as e:
    print(f"Fatal error: {e}")
    import traceback
    traceback.print_exc()
