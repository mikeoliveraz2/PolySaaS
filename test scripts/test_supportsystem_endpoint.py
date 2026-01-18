import requests
import re

url = 'https://polysaas.supportsystem.com/scp/dashboard.php'
print(f'Testing endpoint URL: {url}')
try:
    resp = requests.get(url, timeout=10)
    print(f'Status: {resp.status_code}')
    print(f'Content-Type: {resp.headers.get("Content-Type")}')
    print(f'Content length: {len(resp.content)}')

    # Look for CSS links
    css_pattern = r'<link[^>]*href=["\'][^"\']*\.css[^"\']*["\']'
    css_matches = re.findall(css_pattern, resp.text, re.IGNORECASE)
    print(f'CSS links found: {len(css_matches)}')
    for i, match in enumerate(css_matches[:3]):
        print(f'  {i+1}: {match}')

    # Check if it's a login page or dashboard
    if 'login' in resp.text.lower():
        print('Page appears to be a login page')
    elif 'dashboard' in resp.text.lower():
        print('Page appears to be a dashboard')
    else:
        print('Page type unclear')

except Exception as e:
    print(f'Error: {e}')