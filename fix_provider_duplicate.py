"""
Fix Google OAuth provider - handle duplicate accounts
Deletes the 'dose' provider account if a 'google' one exists
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from allauth.socialaccount.models import SocialApp, SocialAccount, SocialToken

def fix_google_provider():
    print("=" * 80)
    print("FIXING GOOGLE OAUTH PROVIDER - HANDLING DUPLICATES")
    print("=" * 80)

    # Find all dose accounts
    dose_accounts = SocialAccount.objects.filter(provider='dose')
    print(f"\nFound {dose_accounts.count()} SocialAccount(s) with provider='dose'")

    for dose_acc in dose_accounts:
        print(f"\nChecking account for user: {dose_acc.user.username}, UID: {dose_acc.uid}")

        # Check if a google account exists with the same UID
        google_acc = SocialAccount.objects.filter(
            provider='google',
            uid=dose_acc.uid,
            user=dose_acc.user
        ).first()

        if google_acc:
            print(f"  Found duplicate Google account - keeping Google, deleting 'dose'")
            # Delete tokens associated with dose account
            dose_tokens = SocialToken.objects.filter(account=dose_acc)
            print(f"  Deleting {dose_tokens.count()} token(s) from 'dose' account")
            dose_tokens.delete()
            # Delete the dose account
            dose_acc.delete()
            print(f"  Deleted 'dose' account")

            # Show the google account info
            google_tokens = SocialToken.objects.filter(account=google_acc)
            print(f"  Google account has {google_tokens.count()} token(s)")
        else:
            print(f"  No duplicate found - changing 'dose' to 'google'")
            dose_acc.provider = 'google'
            dose_acc.save()
            print(f"  Changed provider to 'google'")

    # Verify final state
    google_accounts = SocialAccount.objects.filter(provider='google')
    print(f"\n" + "=" * 80)
    print(f"FINAL STATE: {google_accounts.count()} SocialAccount(s) with provider='google'")
    for acc in google_accounts:
        tokens = SocialToken.objects.filter(account=acc)
        print(f"  - User: {acc.user.username}, UID: {acc.uid}, Tokens: {tokens.count()}")

    dose_accounts_remaining = SocialAccount.objects.filter(provider='dose')
    if dose_accounts_remaining.exists():
        print(f"\nWARNING: {dose_accounts_remaining.count()} 'dose' account(s) still exist")
    else:
        print(f"\nSUCCESS: All 'dose' accounts have been fixed or removed")

    print("=" * 80)

if __name__ == '__main__':
    fix_google_provider()

