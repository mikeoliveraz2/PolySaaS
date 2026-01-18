import requests
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Create a test client and login
client = Client()
user = User.objects.get(username='olientAdmin')
client.force_login(user)

print('Testing /admin/osticket/css/login.css request...')
response = client.get('/admin/osticket/css/login.css')
print(f'Status: {response.status_code}')
print(f'Content-Type: {response.get("Content-Type")}')
print(f'Content length: {len(response.content)}')

if hasattr(response, 'streaming_content'):
    content = b''.join(response.streaming_content)
    print(f'Actual content length: {len(content)}')
    if len(content) > 0:
        print('First 200 chars of CSS:')
        print(content[:200].decode('utf-8', errors='ignore'))
    else:
        print('CSS content is empty!')
else:
    print('Not a streaming response')