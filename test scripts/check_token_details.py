import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from allauth.socialaccount.models import SocialToken, SocialAccount
from datetime import datetime, timezone

print("=== Checking TomTHall's OAuth tokens ===\n")

user_id = 7  # TomTHall's ID
accounts = SocialAccount.objects.filter(user_id=user_id)

print(f"Found {accounts.count()} social accounts for TomTHall:")
for acc in accounts:
    print(f"\n  Provider: {acc.provider}")
    print(f"  UID: {acc.uid}")

    tokens = SocialToken.objects.filter(account=acc)
    print(f"  Tokens: {tokens.count()}")

    for token in tokens:
        print(f"\n    Token ID: {token.id}")
        print(f"    Access Token (first 30): {token.token[:30]}...")
        print(f"    Token Secret/Refresh (first 30): {token.token_secret[:30] if token.token_secret else 'None'}...")
        print(f"    Expires at: {token.expires_at}")

        if token.expires_at:
            now = datetime.now(timezone.utc)
            if token.expires_at < now:
                print(f"    ⚠️  TOKEN IS EXPIRED!")
                print(f"    Expired {(now - token.expires_at).total_seconds() / 60:.1f} minutes ago")
            else:
                print(f"    ✅ Token valid for {(token.expires_at - now).total_seconds() / 60:.1f} more minutes")
