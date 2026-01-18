#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from allauth.socialaccount.models import SocialApp

try:
    # Get Google social app
    app = SocialApp.objects.get(provider='google')
    print(f"Google App: {app.name}")
    print(f"Client ID: {app.client_id[:20]}...")
    print(f"Client Secret: {app.secret[:10]}...")
    print(f"Key: {app.key}")
    print(f"Sites: {[site.domain for site in app.sites.all()]}")

    # Check if Gmail scopes are configured
    from django.conf import settings

    print("\n=== Django Settings ===")
    if hasattr(settings, 'SOCIALACCOUNT_PROVIDERS'):
        google_config = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
        print(f"Google Provider Config: {google_config}")

        scope = google_config.get('SCOPE', [])
        print(f"Configured Scopes: {scope}")

        # Check for Gmail scopes
        gmail_scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify'
        ]

        print("\n=== Gmail Scope Check ===")
        for gmail_scope in gmail_scopes:
            if gmail_scope in scope:
                print(f"✅ {gmail_scope}")
            else:
                print(f"❌ {gmail_scope} - MISSING!")

        if not any(gs in scope for gs in gmail_scopes):
            print("\n🚨 NO GMAIL SCOPES CONFIGURED!")
            print("This explains why Gmail OAuth isn't working.")
            print("\nTo fix, add Gmail scopes to settings.py:")
            print("""
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',
        }
    }
}
""")
    else:
        print("❌ No SOCIALACCOUNT_PROVIDERS configuration found!")

except SocialApp.DoesNotExist:
    print("ERROR: Google SocialApp not found!")
    print("You need to create a Google OAuth app in Django admin first.")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()