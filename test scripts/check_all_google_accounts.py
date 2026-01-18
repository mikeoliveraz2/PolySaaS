import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialToken, SocialAccount, SocialApp

print("=== All Google Social Accounts ===\n")

google_accounts = SocialAccount.objects.filter(provider='google')
print(f"Total Google SocialAccounts: {google_accounts.count()}\n")

for account in google_accounts:
    print(f"SocialAccount ID={account.id}")
    print(f"  User: {account.user.username} (ID={account.user.id})")
    print(f"  Email: {account.user.email}")
    print(f"  UID: {account.uid}")
    print(f"  Extra data: {account.extra_data.get('email', 'N/A')}")

    # Check for token
    tokens = SocialToken.objects.filter(account=account)
    print(f"  Tokens: {tokens.count()}")
    for token in tokens:
        print(f"    - Token ID={token.id}, Expires: {token.expires_at}")
    print()
