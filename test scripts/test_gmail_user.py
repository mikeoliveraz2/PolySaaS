import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django
django.setup()

import requests
from django.contrib.auth.models import User
from django.test import Client

# Create a test client
client = Client()

# Get a test user (or create one)
try:
    user = User.objects.get(username='olientAdmin')
    print(f"Found user: {user.username}")
except User.DoesNotExist:
    print("No olientAdmin user found")
    users = User.objects.all()
    if users.exists():
        user = users.first()
        print(f"Using first available user: {user.username}")
    else:
        print("No users found!")
        exit()

# Login the user
client.force_login(user)

# Test the Gmail inbox page
print("\n1. Testing Gmail inbox page...")
response = client.get('/dose/gmail-inbox/')
print(f"Gmail inbox page status: {response.status_code}")

# Test the Gmail API endpoint
print("\n2. Testing Gmail API endpoint...")
response = client.get('/dose/gmail-api/gmail/v1/users/me/messages?maxResults=3')
print(f"Gmail API status: {response.status_code}")
print(f"Response: {response.content.decode()[:200]}...")

# Check if user has Google token
from allauth.socialaccount.models import SocialToken
token = None
try:
    token = SocialToken.objects.get(account__user=user, account__provider='google')
    print(f"\n3. User has Google token: YES")
except:
    print(f"\n3. User has Google token: NO")

if not token:
    print("\nREASON: User needs to authenticate with Google OAuth first")
    print("Solution: Go to http://localhost:8000/accounts/google/login/")