"""
Check michael user's admin access and permissions
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount

def main():
    print("\n" + "="*70)
    print("CHECKING MICHAEL USER ADMIN ACCESS")
    print("="*70)

    # Check michael user
    try:
        user = User.objects.get(username='michael')
        print(f"\n✅ User: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   is_staff: {user.is_staff}")
        print(f"   is_superuser: {user.is_superuser}")
        print(f"   is_active: {user.is_active}")

        if not user.is_staff:
            print("\n❌ PROBLEM: michael.is_staff = False")
            print("   User CANNOT access /admin/ without is_staff=True")
            print("\n   FIX: Run fix_michael_permissions.py")
        else:
            print("\n✅ michael can access /admin/")

        # Check social accounts
        social = SocialAccount.objects.filter(user=user)
        print(f"\n📱 Social Accounts: {social.count()}")
        for acc in social:
            print(f"   - {acc.provider}: {acc.extra_data.get('email', 'N/A')}")

    except User.DoesNotExist:
        print("\n❌ User 'michael' not found!")

    print("\n" + "="*70)
    print("CURRENT REDIRECT SETTINGS:")
    print("="*70)

    from django.conf import settings
    print(f"\nLOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")
    print(f"ACCOUNT_ADAPTER: {settings.ACCOUNT_ADAPTER}")
    print(f"SOCIALACCOUNT_ADAPTER: {settings.SOCIALACCOUNT_ADAPTER}")

    print("\n" + "="*70)
    print("EXPECTED BEHAVIOR:")
    print("="*70)
    print("1. Login with Google → Should redirect to /dose/ (landing page)")
    print("2. Manually type /admin/ → Should show Django admin (if is_staff=True)")
    print("3. Admin dashboard should NOT show sign-out/sign-in messages on every load")
    print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    main()
