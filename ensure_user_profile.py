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

    # Update existing UserProfile for superuser
    profile = UserProfile.objects.filter(user=superuser).first()
    if profile:
        profile.tenant = tenant
        profile.use_system_pref = False
        profile.light_theme = "default"
        profile.dark_theme = "dark"
        profile.save()
        print("UserProfile updated for superuser and tenant id=2.")
    else:
        print("No UserProfile found for superuser.")

if __name__ == "__main__":
    main()
