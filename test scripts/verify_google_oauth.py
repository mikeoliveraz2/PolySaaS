"""
Verify Google OAuth setup for Gmail passthrough
Checks user authentication, tokens, and scopes
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
    print("=" * 70)
    print("GOOGLE OAUTH & GMAIL API VERIFICATION")
    print("=" * 70)

    # Check for olientAdmin user
    try:
        user = User.objects.get(username='olientAdmin')
        print(f"\n✅ User found: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Active: {user.is_active}")
    except User.DoesNotExist:
        print("\n❌ User 'olientAdmin' not found!")
        return

    # Check social accounts
    social_accounts = SocialAccount.objects.filter(user=user)
    print(f"\n📱 Social Accounts: {social_accounts.count()}")
    for account in social_accounts:
        print(f"   - {account.provider}: {account.uid}")
        print(f"     Extra data: {account.extra_data.get('email', 'N/A')}")

    # Check social tokens
    social_tokens = SocialToken.objects.filter(account__user=user)
    print(f"\n🔑 OAuth Tokens: {social_tokens.count()}")
    for token in social_tokens:
        print(f"   - Provider: {token.account.provider}")
        print(f"     Expires: {token.expires_at}")
        print(f"     Has access token: {'✅' if token.token else '❌'}")
        print(f"     Has refresh token: {'✅' if token.token_secret else '❌'}")

        # Check token scopes (if stored in extra_data)
        if hasattr(token.account, 'extra_data') and 'scope' in token.account.extra_data:
            scopes = token.account.extra_data['scope']
            print(f"     Scopes: {scopes}")

            # Check for Gmail scopes
            gmail_scopes = [
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.modify'
            ]
            has_gmail = any(scope in scopes for scope in gmail_scopes)
            print(f"     Gmail API access: {'✅' if has_gmail else '❌ MISSING'}")

    # Check Google OAuth app configuration
    print("\n🔧 Google OAuth App Configuration:")
    try:
        google_app = SocialApp.objects.get(provider='google')
        print(f"   ✅ Google app configured")
        print(f"      Client ID: {google_app.client_id[:20]}...")
        print(f"      Secret: {'***' + google_app.secret[-4:] if google_app.secret else 'NOT SET'}")
        print(f"      Sites: {[site.domain for site in google_app.sites.all()]}")
    except SocialApp.DoesNotExist:
        print("   ❌ Google OAuth app NOT configured in admin!")

    # Check settings
    from django.conf import settings
    print("\n⚙️  Settings Check:")
    google_settings = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
    scopes = google_settings.get('SCOPE', [])
    print(f"   Configured scopes ({len(scopes)}):")
    for scope in scopes:
        print(f"      - {scope}")

    gmail_enabled = any('gmail' in s for s in scopes)
    print(f"\n   Gmail API scopes: {'✅ ENABLED' if gmail_enabled else '❌ DISABLED'}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("=" * 70)

    if social_tokens.count() == 0:
        print("⚠️  No OAuth tokens found!")
        print("   ACTION NEEDED: User must re-authenticate with Google")
        print("   1. Log out from Django")
        print("   2. Log in again with Google")
        print("   3. Grant all requested permissions (including Gmail)")
    elif not gmail_enabled:
        print("⚠️  Gmail scopes not in settings!")
        print("   ACTION NEEDED: Update SOCIALACCOUNT_PROVIDERS in settings.py")
    else:
        # Check if existing token has Gmail scopes
        needs_reauth = True
        for token in social_tokens:
            if token.account.provider == 'google':
                extra_data = token.account.extra_data
                if 'scope' in extra_data:
                    if 'gmail' in extra_data['scope']:
                        needs_reauth = False
                        print("✅ Gmail API ready to use!")
                        break

        if needs_reauth:
            print("⚠️  Token doesn't have Gmail scopes!")
            print("   ACTION NEEDED: User must re-authenticate to get new scopes")
            print("   1. Click 'Connect Google Account' in Gmail page")
            print("   2. Or log out and log in again with Google")

    print("=" * 70)

if __name__ == '__main__':
    main()
