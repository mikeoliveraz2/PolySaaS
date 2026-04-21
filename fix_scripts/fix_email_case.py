"""
Fix email case mismatch between olientAdmin and Google
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User

def main():
    print("\n" + "="*70)
    print("FIXING EMAIL CASE MISMATCH")
    print("="*70)

    try:
        olient = User.objects.get(username='olientAdmin')

        print(f"\nCurrent olientAdmin email: '{olient.email}'")
        print(f"Google returns: 'mikeoliveraz@gmail.com'")

        if olient.email != 'mikeoliveraz@gmail.com':
            print(f"\n⚠️  Email mismatch due to case!")
            print(f"   Changing: '{olient.email}' → 'mikeoliveraz@gmail.com'")

            olient.email = 'mikeoliveraz@gmail.com'
            olient.save()

            print(f"   ✅ Email updated!")
        else:
            print(f"\n✅ Email already correct")

        print("\n" + "="*70)
        print("✅ FIXED - Ready for Google login")
        print("="*70)
        print("\nNow when you login with Google:")
        print("1. Google provides: mikeoliveraz@gmail.com")
        print("2. Allauth finds olientAdmin with same email")
        print("3. Auto-connects to olientAdmin")
        print("4. You get full admin access")
        print("="*70 + "\n")

    except User.DoesNotExist:
        print("\n❌ olientAdmin not found!")

if __name__ == '__main__':
    main()
