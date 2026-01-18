#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialToken, SocialAccount

try:
    # Get the user
    user = User.objects.get(username='olientAdmin')
    print(f"User: {user.username} (ID: {user.id})")

    # Delete expired Google tokens
    deleted_tokens = SocialToken.objects.filter(
        account__user=user,
        app__provider='google'
    ).delete()

    print(f"Deleted expired tokens: {deleted_tokens}")

    # Also delete the social account to force fresh auth
    deleted_accounts = SocialAccount.objects.filter(
        user=user,
        provider='google'
    ).delete()

    print(f"Deleted social accounts: {deleted_accounts}")
    print("✅ Cleared expired authentication. User will need to re-authenticate.")

except User.DoesNotExist:
    print("ERROR: User 'olientAdmin' not found!")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()