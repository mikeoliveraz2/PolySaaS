#!/usr/bin/env python
"""
Check Refresh Token

Check if we have a refresh token to automatically refresh the expired access token.
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

User = get_user_model()

def check_refresh_token():
    """Check if refresh token is available."""

    print("🔄 Checking Refresh Token")
    print("="*30)

    # Get user and token
    user = User.objects.get(username='olientAdmin')
    token = SocialToken.objects.get(account__user=user, account__provider__iexact='google')

    print(f"📱 User: {user.username}")
    print(f"🔑 Access token expires: {token.expires_at}")
    print(f"🔄 Refresh token exists: {'✅ YES' if token.token_secret else '❌ NO'}")

    if token.token_secret:
        print(f"🔄 Refresh token (first 20): {token.token_secret[:20]}...")
        print(f"\n💡 We can implement automatic token refresh!")
        print(f"   Using refresh token to get new access token")
    else:
        print(f"\n❌ No refresh token available")
        print(f"💡 User must re-authenticate with Google")
        print(f"   Steps to fix:")
        print(f"   1. Logout: http://localhost:8000/accounts/logout/")
        print(f"   2. Re-login: http://localhost:8000/accounts/google/login/")

if __name__ == "__main__":
    check_refresh_token()