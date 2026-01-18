#!/usr/bin/env python
"""
Setup Google OAuth2 for Django Allauth
Creates a SocialApp with Google credentials
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

def setup_google_oauth():
    print("=" * 60)
    print("Google OAuth2 Setup for DOSE")
    print("=" * 60)

    # Get or create the default site
    site = Site.objects.get_current()
    print(f"\n✓ Current site: {site.domain} (ID: {site.id})")

    # Check if Google app already exists
    existing_app = SocialApp.objects.filter(provider='google').first()

    if existing_app:
        print(f"\n⚠️  Google SocialApp already exists: {existing_app.name}")
        print(f"   Client ID: {existing_app.client_id[:20]}...")
        update = input("\nDo you want to update it? (y/n): ").lower().strip()
        if update != 'y':
            print("Exiting without changes.")
            return
        app = existing_app
    else:
        print("\n✓ No existing Google app found. Creating new one...")
        app = SocialApp(provider='google', name='Google OAuth2')

    # Get credentials
    print("\n" + "=" * 60)
    print("GOOGLE OAUTH2 CREDENTIALS")
    print("=" * 60)
    print("\nYou need to get these from Google Cloud Console:")
    print("https://console.cloud.google.com/apis/credentials")
    print("\nMake sure to add these authorized redirect URIs:")
    print("  - http://127.0.0.1:8000/accounts/google/login/callback/")
    print("  - http://localhost:8000/accounts/google/login/callback/")
    print("\n" + "=" * 60)

    client_id = input("\nEnter Google Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required!")
        return

    client_secret = input("Enter Google Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret is required!")
        return

    # Update app
    app.client_id = client_id
    app.secret = client_secret
    app.save()

    # Add site if not already added
    if site not in app.sites.all():
        app.sites.add(site)
        print(f"\n✓ Added site '{site.domain}' to Google app")

    print("\n" + "=" * 60)
    print("✅ GOOGLE OAUTH2 CONFIGURED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\nApp Name: {app.name}")
    print(f"Provider: {app.provider}")
    print(f"Client ID: {app.client_id[:20]}...")
    print(f"Client Secret: {app.secret[:10]}...")
    print(f"Sites: {', '.join([s.domain for s in app.sites.all()])}")

    print("\n" + "=" * 60)
    print("CONFIGURED SCOPES (from settings.py):")
    print("=" * 60)
    from django.conf import settings
    google_config = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
    scopes = google_config.get('SCOPE', [])
    for scope in scopes:
        print(f"  ✓ {scope}")

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Start the Django server: python manage.py runserver")
    print("2. Navigate to: http://127.0.0.1:8000/accounts/login/")
    print("3. Click 'Sign in with Google'")
    print("4. Test the OAuth flow")
    print("\n✨ Done!")

if __name__ == '__main__':
    setup_google_oauth()
