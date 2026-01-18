import requests
import django
import os
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

# Check what the endpoint URL actually returns
endpoint_url = 'https://oliverenterprises.app.saasify.cloud/scp/'

print('Fetching endpoint URL directly...')
try:
    resp = requests.get(endpoint_url, timeout=10)
    print(f'Status: {resp.status_code}')
    print(f'Content-Type: {resp.headers.get("Content-Type")}')
    print(f'Content length: {len(resp.content)}')

    # Look for CSS links in the HTML
    css_pattern = r'<link[^>]*href=["\'][^"\']*\.css[^"\']*["\']'
    css_matches = re.findall(css_pattern, resp.text, re.IGNORECASE)
    print(f'CSS link tags found: {len(css_matches)}')
    for i, match in enumerate(css_matches[:5]):  # Show first 5
        print(f'  {i+1}: {match}')

    # Look for the title or any indication of what page this is
    title_match = re.search(r'<title[^>]*>([^<]*)</title>', resp.text, re.IGNORECASE)
    if title_match:
        print(f'Page title: {title_match.group(1).strip()}')

    # Check if this is a login page
    if 'login' in resp.text.lower():
        print('Page appears to be a login page')
    else:
        print('Page does NOT appear to be a login page')

except Exception as e:
    print(f'Error fetching endpoint: {e}')