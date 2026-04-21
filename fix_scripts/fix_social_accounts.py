"""
Detailed check of ALL social accounts
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp

def main():
    print("\n" + "="*70)
    print("DETAILED SOCIAL ACCOUNT ANALYSIS")
    print("="*70)

    # Check all social accounts
    all_accounts = SocialAccount.objects.all()
    print(f"\n📊 Total Social Accounts: {all_accounts.count()}\n")

    for acc in all_accounts:
        print(f"{'='*70}")
        print(f"ID: {acc.id}")
        print(f"User: {acc.user.username}")
        print(f"Provider: {acc.provider}")
        print(f"UID: {acc.uid}")
        print(f"Extra Data: {acc.extra_data}")
        print()

    # Check social apps
    print("="*70)
    print("CONFIGURED SOCIAL APPS:")
    print("="*70)
    apps = SocialApp.objects.all()
    for app in apps:
        print(f"\n{app.provider}:")
        print(f"  Client ID: {app.client_id[:20]}...")
        print(f"  Sites: {[site.domain for site in app.sites.all()]}")

    # Fix if provider is 'dose' instead of 'google'
    print("\n" + "="*70)
    print("CHECKING FOR MISNAMED PROVIDERS:")
    print("="*70)

    dose_provider = SocialAccount.objects.filter(provider='dose')
    if dose_provider.exists():
        print(f"\n⚠️  Found {dose_provider.count()} account(s) with provider='dose' (should be 'google')")
        for acc in dose_provider:
            print(f"\n   Account ID: {acc.id}")
            print(f"   User: {acc.user.username}")
            print(f"   Email: {acc.extra_data.get('email', 'N/A')}")

            response = input(f"\n   Fix this account? Change provider from 'dose' to 'google'? (y/n): ")
            if response.lower() == 'y':
                acc.provider = 'google'
                acc.save()
                print(f"   ✅ Fixed! Provider is now 'google'")

                # Now transfer to olientAdmin if it's michael's account
                if acc.user.username == 'michael':
                    print(f"\n   This is michael's account. Transfer to olientAdmin? (y/n): ")
                    transfer = input("   ")
                    if transfer.lower() == 'y':
                        olient = User.objects.get(username='olientAdmin')
                        acc.user = olient
                        acc.save()
                        print(f"   ✅ Transferred to olientAdmin!")
    else:
        print("\n✅ No misnamed providers found")

    print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    main()
