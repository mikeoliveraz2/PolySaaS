"""
Show the exact OAuth redirect URIs that need to be configured in Google Cloud Console
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

print("\n" + "="*70)
print("GOOGLE OAUTH REDIRECT URI CONFIGURATION")
print("="*70)

# Get all sites associated with Google OAuth
try:
    google_app = SocialApp.objects.get(provider='google')
    sites = google_app.sites.all()

    print("\n📋 ADD THESE REDIRECT URIs TO GOOGLE CLOUD CONSOLE:")
    print("-" * 70)

    redirect_uris = []
    for site in sites:
        # HTTP redirect URI
        http_uri = f"http://{site.domain}/accounts/google/login/callback/"
        redirect_uris.append(http_uri)

        # HTTPS redirect URI (for production)
        if site.domain not in ['127.0.0.1:8000', 'localhost:8000', '127.0.0.1', 'localhost']:
            https_uri = f"https://{site.domain}/accounts/google/login/callback/"
            redirect_uris.append(https_uri)

    # Display all URIs
    for i, uri in enumerate(redirect_uris, 1):
        print(f"{i}. {uri}")

    print("\n" + "="*70)
    print("STEPS TO FIX:")
    print("="*70)
    print("1. Go to: https://console.cloud.google.com/apis/credentials")
    print("2. Find your OAuth 2.0 Client ID")
    print("3. Click Edit")
    print("4. Under 'Authorized redirect URIs', add the URIs listed above")
    print("5. Click Save")
    print("6. Wait a few minutes for changes to propagate")
    print("7. Try logging in again")
    print("="*70)

    print("\n💡 TIP: Copy and paste each URI exactly as shown above")
    print("\n")

except SocialApp.DoesNotExist:
    print("\n❌ ERROR: Google SocialApp not found!")
    print("Run: python setup_google_oauth.py")
