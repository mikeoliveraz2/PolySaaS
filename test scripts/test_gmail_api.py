#!/usr/bin/env python
import os
import django
import requests
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from allauth.socialaccount.models import SocialToken
from django.contrib.auth.models import User

print("=== TESTING GMAIL API CALLS ===")
print()

# Get the authenticated user's token
try:
    user = User.objects.get(username='olientAdmin')
    print(f"Testing Gmail API for user: {user.username}")
    print(f"User email: {user.email}")

    # Get the Google OAuth token
    token_obj = SocialToken.objects.get(
        account__user=user,
        account__provider__iexact='google'
    )

    oauth_token = token_obj.token
    print(f"Token found: {oauth_token[:30]}...")
    print(f"Token expires: {token_obj.expires_at}")
    print()

    # Test Gmail API calls
    headers = {
        'Authorization': f'Bearer {oauth_token}',
        'Content-Type': 'application/json'
    }

    print("=== TESTING GMAIL API ENDPOINTS ===")

    # Test 1: Get user profile
    print("1. Testing Gmail Profile API...")
    profile_url = 'https://gmail.googleapis.com/gmail/v1/users/me/profile'
    try:
        response = requests.get(profile_url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            profile_data = response.json()
            print(f"   Email: {profile_data.get('emailAddress')}")
            print(f"   Messages Total: {profile_data.get('messagesTotal')}")
            print(f"   Threads Total: {profile_data.get('threadsTotal')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

    print()

    # Test 2: List messages (first 5)
    print("2. Testing Gmail Messages API...")
    messages_url = 'https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=5'
    try:
        response = requests.get(messages_url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            messages_data = response.json()
            messages = messages_data.get('messages', [])
            print(f"   Found {len(messages)} messages")
            for i, msg in enumerate(messages[:3]):
                print(f"     - Message {i+1}: {msg['id']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

    print()

    # Test 3: List labels
    print("3. Testing Gmail Labels API...")
    labels_url = 'https://gmail.googleapis.com/gmail/v1/users/me/labels'
    try:
        response = requests.get(labels_url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            labels_data = response.json()
            labels = labels_data.get('labels', [])
            print(f"   Found {len(labels)} labels")
            for label in labels[:5]:
                print(f"     - {label['name']} ({label['id']})")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

    print()

    # Test 4: Check OAuth token info
    print("4. Testing OAuth Token Info...")
    token_info_url = f'https://oauth2.googleapis.com/tokeninfo?access_token={oauth_token}'
    try:
        response = requests.get(token_info_url)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            token_info = response.json()
            print(f"   Scopes: {token_info.get('scope')}")
            print(f"   Expires in: {token_info.get('expires_in')} seconds")
            print(f"   Audience: {token_info.get('aud')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")

except SocialToken.DoesNotExist:
    print("ERROR: No Google OAuth token found for olientAdmin")
except User.DoesNotExist:
    print("ERROR: User olientAdmin not found")
except Exception as e:
    print(f"ERROR: {e}")

print("\n=== TEST COMPLETE ===")