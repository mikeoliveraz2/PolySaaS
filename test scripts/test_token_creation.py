#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialToken, SocialAccount, SocialApp
from django.utils import timezone
from datetime import timedelta, datetime

try:
    # Get the user and social account
    user = User.objects.get(username='olientAdmin')
    google_app = SocialApp.objects.get(provider='google')
    social_account = SocialAccount.objects.get(user=user, provider='google')

    print(f"User: {user.username}")
    print(f"Social Account: {social_account.uid}")
    print(f"Google App: {google_app.name}")

    # The issue might be that we need to manually trigger a token refresh
    # Let's try to see what happens when we manually call the allauth token logic

    print(f"\n=== Manual Token Creation Test ===")

    # Create a test token to see if the database accepts it
    test_token = SocialToken(
        app=google_app,
        account=social_account,
        token="test_token_12345",
        token_secret="",
        expires_at=timezone.now() + timedelta(hours=1)
    )

    try:
        test_token.save()
        print(f"✅ Test token created successfully: {test_token.id}")

        # Now try to retrieve it the same way the Gmail service does
        retrieved_token = SocialToken.objects.get(
            account__user=user,
            app__provider='google'
        )
        print(f"✅ Retrieved token: {retrieved_token.token}")

        # Clean up test token
        test_token.delete()
        print(f"✅ Test token cleaned up")

        print(f"\n🎯 DATABASE IS WORKING! The issue is in the OAuth flow, not the database.")
        print(f"The OAuth callback isn't creating the token properly.")

    except Exception as e:
        print(f"❌ Database issue: {e}")

    # Let's check the OAuth callback URL configuration
    print(f"\n=== OAuth URL Check ===")
    from django.conf import settings

    if hasattr(settings, 'SITE_ID'):
        print(f"SITE_ID: {settings.SITE_ID}")

    # Check if the social account has the right permissions
    print(f"\nSocial Account Extra Data:")
    for key, value in social_account.extra_data.items():
        print(f"  {key}: {value}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()