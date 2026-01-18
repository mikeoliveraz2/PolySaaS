import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth.models import User
from dose.models import Tenant, UserProfile

def main():
    # Find superuser
    superuser = User.objects.filter(is_superuser=True).first()
    if not superuser:
        print("No superuser found.")
        return

    # Find tenant with id=2
    tenant = Tenant.objects.filter(id=2).first()
    if not tenant:
        print("No tenant with id=2 found.")
        return

    # Print UserProfile values
    profile = UserProfile.objects.filter(user=superuser, tenant=tenant).first()
    if profile:
        print(f"UserProfile for user={superuser.username}, tenant={tenant.id}:")
        print(f"  light_theme: {profile.light_theme}")
        print(f"  dark_theme: {profile.dark_theme}")
        print(f"  last_selected_theme: {profile.last_selected_theme}")
    else:
        print("No UserProfile found for superuser and tenant id=2.")

if __name__ == "__main__":
    main()
