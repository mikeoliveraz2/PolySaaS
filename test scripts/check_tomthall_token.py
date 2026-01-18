import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialToken, SocialAccount, SocialApp

print("=== Checking TomTHall OAuth Token ===\n")

# Find TomTHall user
user = User.objects.filter(username='TomTHall').first()
if not user:
    print("ERROR: TomTHall user not found!")
    exit()

print(f"User: {user.username} (ID={user.id})")
print()

# Check for Google SocialAccount
google_accounts = SocialAccount.objects.filter(user=user, provider='google')
print(f"Google SocialAccounts: {google_accounts.count()}")
for account in google_accounts:
    print(f"  - Account ID={account.id}, UID={account.uid}, extra_data={list(account.extra_data.keys())}")
print()

# Check for Google SocialToken
google_tokens = SocialToken.objects.filter(account__user=user, account__provider='google')
print(f"Google SocialTokens: {google_tokens.count()}")
for token in google_tokens:
    print(f"  - Token ID={token.id}")
    print(f"    Account: {token.account.provider} ({token.account.uid})")
    print(f"    Token: {token.token[:20]}..." if token.token else "    Token: None")
    print(f"    Token Secret: {token.token_secret[:20] if token.token_secret else 'None'}...")
    print(f"    Expires: {token.expires_at}")
print()

# Check SocialApp configuration
google_apps = SocialApp.objects.filter(provider='google')
print(f"Google SocialApp configuration: {google_apps.count()}")
for app in google_apps:
    print(f"  - App ID={app.id}, Name={app.name}")
    print(f"    Client ID: {app.client_id[:20]}...")
    print(f"    Secret configured: {'Yes' if app.secret else 'No'}")
    print(f"    Sites: {[site.domain for site in app.sites.all()]}")
print()

if google_tokens.count() == 0:
    print("❌ NO TOKEN FOUND - This is why the OAuth loop continues!")
    print("\nPossible causes:")
    print("1. SOCIALACCOUNT_STORE_TOKENS = False in settings")
    print("2. OAuth scope doesn't include offline access")
    print("3. Token not being saved after successful OAuth")
    print("4. Session/cookie issue preventing token storage")
else:
    print(f"✓ Token exists - OAuth should work")
