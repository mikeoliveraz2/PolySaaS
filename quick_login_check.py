"""
Quick check: Who is currently logged in via Google?
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from django.contrib.sessions.models import Session
from django.utils import timezone

def main():
    print("\n" + "="*70)
    print("CURRENT LOGIN STATUS CHECK")
    print("="*70)

    # Check all users
    print("\n📊 All Users:")
    users = User.objects.all()
    for user in users:
        social = SocialAccount.objects.filter(user=user, provider='google')
        google = f" [Google: {social.first().extra_data.get('email')}]" if social.exists() else ""
        staff = "✅ STAFF" if user.is_staff else "❌ NOT STAFF"
        print(f"   {user.username} ({user.email}){google} - {staff}")

    # Check active sessions
    print("\n🔑 Active Sessions:")
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    print(f"   Total: {active_sessions.count()}")

    for session in active_sessions:
        session_data = session.get_decoded()
        user_id = session_data.get('_auth_user_id')
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                print(f"   - {user.username} (expires: {session.expire_date})")
            except User.DoesNotExist:
                print(f"   - Unknown user ID: {user_id}")

    # Check if there's a user with mikeoliveraz@gmail.com
    print("\n🔍 Users with mikeoliveraz@gmail.com:")
    matching = User.objects.filter(email__iexact='mikeoliveraz@gmail.com')
    if matching.exists():
        for user in matching:
            print(f"   {user.username}:")
            print(f"      is_staff: {user.is_staff}")
            print(f"      is_active: {user.is_active}")
            print(f"      is_superuser: {user.is_superuser}")

            social = SocialAccount.objects.filter(user=user)
            if social.exists():
                print(f"      Google connected: ✅")
            else:
                print(f"      Google connected: ❌")
    else:
        print("   None found")

    print("\n" + "="*70)
    print("DIAGNOSIS:")
    print("="*70)

    # Find the issue
    google_accounts = SocialAccount.objects.filter(provider='google')
    if google_accounts.count() == 0:
        print("❌ NO Google accounts connected!")
        print("   → When you login with Google, a NEW user is being created")
        print("   → Need to check SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT")
    else:
        for acc in google_accounts:
            user = acc.user
            if not user.is_staff:
                print(f"⚠️  User {user.username} has Google connected but is_staff=False")
                print(f"   → Setting is_staff=True now...")
                user.is_staff = True
                user.save()
                print(f"   ✅ Fixed!")
            else:
                print(f"✅ User {user.username} has Google connected and is_staff=True")

    print("="*70 + "\n")

if __name__ == '__main__':
    main()
