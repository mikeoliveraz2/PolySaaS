import requests
import django
import os
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Create a test client and login
client = Client()
user = User.objects.get(username='olientAdmin')
client.force_login(user)

print('Testing /admin/osticket/ request to see what CSS URLs are processed...')
response = client.get('/admin/osticket/')
print(f'Status: {response.status_code}')
print(f'Content-Type: {response.get("Content-Type")}')

# Look for CSS links in the response
css_links = re.findall(r'<link[^>]*href=["\'][^"\']*\.css[^"\']*["\']', response.content.decode('utf-8', errors='ignore'), re.IGNORECASE)
print(f'CSS links in processed HTML: {len(css_links)}')
for i, link in enumerate(css_links[:5]):
    print(f'  {i+1}: {link}')

# Also check for any mentions of osticket.css vs login.css
content = response.content.decode('utf-8', errors='ignore')
if 'osticket.css' in content:
    print('Found osticket.css in response')
if 'login.css' in content:
    print('Found login.css in response')