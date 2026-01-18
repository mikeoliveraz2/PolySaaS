"""
Create UserProfile for user 7 (TomTHall)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import UserProfile, Tenant
from django.contrib.auth.models import User

try:
    user = User.objects.get(id=7)
    print(f"User found: {user.username} (ID: {user.id})")

    # Get or create default tenant
    default_tenant, created = Tenant.objects.get_or_create(
        slug='public',
        defaults={
            'name': 'Public Tenant',
            'description': 'Default tenant for all users',
            'is_active': True
        }
    )

    if created:
        print(f"Created default tenant: {default_tenant.name}")
    else:
        print(f"Using existing tenant: {default_tenant.name}")

    # Create UserProfile
    profile, profile_created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'tenant': default_tenant}
    )

    if profile_created:
        print(f"✅ Created UserProfile for {user.username} with tenant {default_tenant.name}")
    else:
        print(f"ℹ️ UserProfile already exists for {user.username} (tenant: {profile.tenant.name if profile.tenant else 'None'})")

except User.DoesNotExist:
    print("❌ User 7 does not exist")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
