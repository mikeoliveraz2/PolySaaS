"""
Check what user was created by Google login and fix staff permissions
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
    print("CHECKING GOOGLE LOGIN - USER PERMISSIONS")
    print("="*70)

    # Show all users
    users = User.objects.all().order_by('-date_joined')
    print(f"\n📊 All Users (newest first):\n")

    for user in users:
        print(f"{'='*70}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"is_staff: {user.is_staff} {'✅' if user.is_staff else '❌'}")
        print(f"is_superuser: {user.is_superuser}")
        print(f"is_active: {user.is_active}")
        print(f"Date joined: {user.date_joined}")

        # Check social accounts
        social = SocialAccount.objects.filter(user=user)
        if social.exists():
            for acc in social:
                print(f"🔗 Google: {acc.extra_data.get('email', 'N/A')} (provider: {acc.provider})")
        print()

    # Find users with Google accounts that aren't staff
    print("="*70)
    print("FIXING NON-STAFF USERS WITH GOOGLE ACCOUNTS:")
    print("="*70)

    google_users = SocialAccount.objects.filter(provider='google')
    fixed_count = 0

    for social_acc in google_users:
        user = social_acc.user
        google_email = social_acc.extra_data.get('email', 'N/A')

        if not user.is_staff:
            print(f"\n⚠️  User '{user.username}' (Google: {google_email}) is NOT staff")
            print(f"   Setting is_staff=True...")

            user.is_staff = True
            user.save()

            print(f"   ✅ Fixed! {user.username} is now staff")
            fixed_count += 1
        else:
            print(f"\n✅ User '{user.username}' (Google: {google_email}) already has staff access")

    if fixed_count > 0:
        print(f"\n" + "="*70)
        print(f"✅ Fixed {fixed_count} user(s)")
        print("="*70)
        print("\nNow try accessing /admin/ again - it should work!")
    else:
        print(f"\n" + "="*70)
        print("All Google users already have staff access")
        print("="*70)

    print("\n")

if __name__ == '__main__':
    main()
