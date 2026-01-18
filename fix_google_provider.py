"""
Fix Google OAuth provider ID in database
The provider is incorrectly set to 'dose' instead of 'google'
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from allauth.socialaccount.models import SocialApp, SocialAccount, SocialToken
from django.contrib.sites.models import Site

def fix_google_provider():
    print("=" * 80)
    print("FIXING GOOGLE OAUTH PROVIDER")
    print("=" * 80)

    # Check current SocialApp entries
    print("\nCurrent SocialApp entries:")
    for app in SocialApp.objects.all():
        print(f"  - Provider: {app.provider}, Name: {app.name}, Client ID: {app.client_id[:20]}...")

    # Find the incorrectly configured app
    dose_apps = SocialApp.objects.filter(provider='dose')
    if dose_apps.exists():
        print(f"\n⚠️  Found {dose_apps.count()} SocialApp(s) with provider='dose' (INCORRECT)")
        for app in dose_apps:
            print(f"\n  Fixing SocialApp: {app.name}")
            print(f"    OLD: provider='{app.provider}'")
            app.provider = 'google'
            app.save()
            print(f"    NEW: provider='{app.provider}'")

    # Fix existing SocialAccount entries
    dose_accounts = SocialAccount.objects.filter(provider='dose')
    if dose_accounts.exists():
        print(f"\n⚠️  Found {dose_accounts.count()} SocialAccount(s) with provider='dose' (INCORRECT)")
        for acc in dose_accounts:
            print(f"\n  Fixing SocialAccount for user: {acc.user.username}")
            print(f"    OLD: provider='{acc.provider}', UID: {acc.uid}")
            acc.provider = 'google'
            acc.save()
            print(f"    NEW: provider='{acc.provider}', UID: {acc.uid}")

            # Update associated tokens
            tokens = SocialToken.objects.filter(account=acc)
            for token in tokens:
                print(f"    - Token expires: {token.expires_at}")

    # Verify Google SocialApp exists and is configured
    google_apps = SocialApp.objects.filter(provider='google')
    if not google_apps.exists():
        print("\n❌ ERROR: No SocialApp with provider='google' found!")
        print("   You need to create one in Django Admin:")
        print("   - Provider: google")
        print("   - Name: Google")
        print("   - Client ID: (from Google Cloud Console)")
        print("   - Secret key: (from Google Cloud Console)")
        print("   - Sites: localhost:8000 (Site ID 1)")
    else:
        print(f"\n✅ Found {google_apps.count()} SocialApp(s) with provider='google':")
        for app in google_apps:
            print(f"  - Name: {app.name}")
            print(f"    Client ID: {app.client_id[:20]}...")
            print(f"    Sites: {[site.domain for site in app.sites.all()]}")

    # Verify fixed accounts
    google_accounts = SocialAccount.objects.filter(provider='google')
    print(f"\n✅ Total SocialAccounts with provider='google': {google_accounts.count()}")
    for acc in google_accounts:
        print(f"  - User: {acc.user.username}, UID: {acc.uid}")
        tokens = SocialToken.objects.filter(account=acc)
        print(f"    Tokens: {tokens.count()}")
        for token in tokens:
            print(f"      - Expires: {token.expires_at}")

    print("\n" + "=" * 80)
    print("DONE")
    print("=" * 80)

if __name__ == '__main__':
    fix_google_provider()
