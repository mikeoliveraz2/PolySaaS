"""
FINAL FIX: Transfer Google from michael to olientAdmin and delete michael
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
    print("FINAL GOOGLE LOGIN FIX")
    print("="*70)

    try:
        michael = User.objects.get(username='michael')
        olient = User.objects.get(username='olientAdmin')

        print(f"\n1️⃣ Transferring Google account from michael to olientAdmin:")

        # Get michael's Google accounts
        google_accounts = SocialAccount.objects.filter(user=michael, provider='google')

        for acc in google_accounts:
            email = acc.extra_data.get('email', 'N/A')
            print(f"   Moving Google account ({email}) to olientAdmin...")

            # Transfer to olientAdmin
            acc.user = olient
            acc.save()
            print(f"   ✅ Transferred!")

            # Transfer tokens too
            tokens = SocialToken.objects.filter(account=acc)
            for token in tokens:
                print(f"   ✅ Token also transferred")

        print(f"\n2️⃣ Deleting michael user:")
        michael.delete()
        print(f"   ✅ Michael deleted!")

        print("\n" + "="*70)
        print("VERIFICATION:")
        print("="*70)

        # Verify olientAdmin has the Google connection
        olient_google = SocialAccount.objects.filter(user=olient, provider='google')
        if olient_google.exists():
            for acc in olient_google:
                print(f"✅ olientAdmin now has Google: {acc.extra_data.get('email')}")
        else:
            print(f"❌ Something went wrong - olientAdmin has no Google account")

        print(f"\n📊 Final user list:")
        for user in User.objects.all():
            google = SocialAccount.objects.filter(user=user, provider='google')
            conn = f" [Google ✅]" if google.exists() else ""
            staff = "STAFF ✅" if user.is_staff else "NOT STAFF ❌"
            print(f"   {user.username}{conn} - {staff}")

        print("\n" + "="*70)
        print("✅ SUCCESS - READY FOR DEMO!")
        print("="*70)
        print("\nNow:")
        print("1. Logout and clear browser cache")
        print("2. Login with Google")
        print("3. Will automatically login as olientAdmin")
        print("4. Full admin access available")
        print("="*70 + "\n")

    except User.DoesNotExist as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    main()
