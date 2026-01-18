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

    # Show first 1000 chars to see what the page looks like
    print('\n--- First 1000 chars of response ---')
    print(resp.text[:1000])
    print('--- End first 1000 chars ---\n')

    # Look for CSS links in the HTML
    css_pattern = r'<link[^>]*href=["\'][^"\']*\.css[^"\']*["\']'
    css_matches = re.findall(css_pattern, resp.text, re.IGNORECASE)
    print(f'CSS link tags found: {len(css_matches)}')
    for i, match in enumerate(css_matches):
        print(f'  {i+1}: {match}')

    # Look for the title
    title_match = re.search(r'<title[^>]*>([^<]*)</title>', resp.text, re.IGNORECASE)
    if title_match:
        print(f'Page title: {title_match.group(1).strip()}')

    # Check for error messages
    if 'error' in resp.text.lower() or '422' in resp.text:
        print('Page contains error messages')
        error_matches = re.findall(r'<div[^>]*class=["\'][^"\']*error[^"\']*["\'][^>]*>(.*?)</div>', resp.text, re.DOTALL | re.IGNORECASE)
        if error_matches:
            print('Error messages found:')
            for error in error_matches[:3]:
                print(f'  {error.strip()[:200]}...')

except Exception as e:
    print(f'Error fetching endpoint: {e}')