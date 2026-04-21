"""
Fix Google OAuth provider ID in database
Changes provider from 'dose' to 'google'
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from allauth.socialaccount.models import SocialApp, SocialAccount, SocialToken

def fix_google_provider():
    print("=" * 80)
    print("FIXING GOOGLE OAUTH PROVIDER")
    print("=" * 80)

    # Fix SocialApp entries
    dose_apps = SocialApp.objects.filter(provider='dose')
    if dose_apps.exists():
        print(f"\nFound {dose_apps.count()} SocialApp(s) with provider='dose' (INCORRECT)")
        for app in dose_apps:
            print(f"  Fixing SocialApp: {app.name}")
            print(f"    OLD: provider='{app.provider}'")
            app.provider = 'google'
            app.save()
            print(f"    NEW: provider='{app.provider}'")

    # Fix SocialAccount entries
    dose_accounts = SocialAccount.objects.filter(provider='dose')
    if dose_accounts.exists():
        print(f"\nFound {dose_accounts.count()} SocialAccount(s) with provider='dose' (INCORRECT)")
        for acc in dose_accounts:
            print(f"  Fixing SocialAccount for user: {acc.user.username}")
            print(f"    OLD: provider='{acc.provider}', UID: {acc.uid}")
            acc.provider = 'google'
            acc.save()
            print(f"    NEW: provider='{acc.provider}', UID: {acc.uid}")

    # Verify Google accounts
    google_accounts = SocialAccount.objects.filter(provider='google')
    print(f"\nTotal SocialAccounts with provider='google': {google_accounts.count()}")
    for acc in google_accounts:
        print(f"  - User: {acc.user.username}, UID: {acc.uid}")
        tokens = SocialToken.objects.filter(account=acc)
        print(f"    Tokens: {tokens.count()}")

    print("\n" + "=" * 80)
    print("DONE")
    print("=" * 80)

if __name__ == '__main__':
    fix_google_provider()

