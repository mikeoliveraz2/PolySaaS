"""
Check which Django users are connected to which Google accounts
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialToken

def main():
    print("\n" + "="*70)
    print("GOOGLE ACCOUNT MAPPING CHECK")
    print("="*70)

    # Get all users
    users = User.objects.all()
    print(f"\n📊 Total Users: {users.count()}\n")

    for user in users:
        print(f"👤 {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Staff: {user.is_staff} | Superuser: {user.is_superuser}")

        # Check social accounts
        social_accounts = SocialAccount.objects.filter(user=user)
        if social_accounts.exists():
            for acc in social_accounts:
                google_email = acc.extra_data.get('email', 'N/A')
                print(f"   🔗 Google Account: {google_email}")
                print(f"      Provider: {acc.provider}")
                print(f"      UID: {acc.uid}")
        else:
            print(f"   ⚠️  No Google account connected")
        print()

    # Summary
    print("="*70)
    print("ISSUE DIAGNOSIS:")
    print("="*70)

    google_accounts = SocialAccount.objects.filter(provider='google')
    print(f"\n📱 Total Google connections: {google_accounts.count()}\n")

    for acc in google_accounts:
        google_email = acc.extra_data.get('email', 'N/A')
        print(f"   {google_email} → Django user: {acc.user.username}")

    print("\n" + "="*70)
    print("SOLUTION:")
    print("="*70)
    print("\nIf you want to login as olientAdmin with Google:")
    print("1. Login as michael (current)")
    print("2. Go to /admin/socialaccount/socialaccount/")
    print("3. DELETE michael's Google connection")
    print("4. Logout")
    print("5. Login with Google using olientAdmin's email")
    print("\nOR simply use olientAdmin's email when logging in with Google")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
