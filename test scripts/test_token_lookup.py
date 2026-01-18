#!/usr/bin/env python
"""
Test OAuth Token Lookup

Simple test to check if the token lookup works exactly as in the Gmail service.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from allauth.socialaccount.models import SocialToken
from django.contrib.auth import get_user_model
from datetime import datetime, timezone

User = get_user_model()

def test_token_lookup():
    """Test the exact token lookup logic used in Gmail service."""

    print("🔍 Testing OAuth Token Lookup")
    print("="*40)

    # Get user
    user = User.objects.get(username='olientAdmin')
    print(f"✅ User: {user.username}")

    # Test the exact lookup used in Gmail service
    try:
        token_obj = SocialToken.objects.get(
            account__user=user,
            account__provider__iexact='google'
        )
        oauth_token = token_obj.token
        print(f"✅ Token found!")
        print(f"   Token (first 30 chars): {oauth_token[:30]}...")
        print(f"   Token length: {len(oauth_token)}")
        print(f"   Expires: {token_obj.expires_at}")

        # Check expiration
        if token_obj.expires_at:
            now = datetime.now(timezone.utc)
            is_expired = token_obj.expires_at <= now
            print(f"   Is expired: {'❌ YES' if is_expired else '✅ NO'}")
            if is_expired:
                seconds_ago = (now - token_obj.expires_at).total_seconds()
                print(f"   ⏰ Expired {seconds_ago:.0f} seconds ago")
                print(f"   🔧 SOLUTION: User needs to re-authenticate!")

        return oauth_token, is_expired if token_obj.expires_at else False

    except SocialToken.DoesNotExist:
        print("❌ No OAuth token found!")
        return None, False

if __name__ == "__main__":
    token, expired = test_token_lookup()

    if token and not expired:
        print(f"\n🧪 Testing API call with token:")
        import requests
        headers = {'Authorization': f'Bearer {token}'}

        try:
            response = requests.get(
                'https://gmail.googleapis.com/gmail/v1/users/me/profile',
                headers=headers,
                timeout=10
            )
            print(f"   📧 Gmail API Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success! Email: {data.get('emailAddress')}")
            else:
                print(f"   ❌ Failed: {response.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")