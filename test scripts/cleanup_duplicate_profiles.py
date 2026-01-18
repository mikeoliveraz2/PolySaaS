"""
Cleanup script to remove duplicate UserProfile entries
Run this before editing users in admin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import UserProfile
from django.contrib.auth.models import User

print("Checking for duplicate UserProfile entries...")

# Find users with multiple profiles
from django.db.models import Count

duplicates = User.objects.annotate(
    profile_count=Count('userprofile')
).filter(profile_count__gt=1)

if duplicates.exists():
    print(f"\nFound {duplicates.count()} users with duplicate profiles:")
    for user in duplicates:
        profiles = UserProfile.objects.filter(user=user)
        print(f"\n  User: {user.username} (ID: {user.id})")
        print(f"  Profile count: {profiles.count()}")

        # Keep the first one, delete the rest
        first_profile = profiles.first()
        duplicates_to_delete = profiles.exclude(id=first_profile.id)

        if duplicates_to_delete.exists():
            print(f"  Keeping profile ID: {first_profile.id} (tenant: {first_profile.tenant.name if first_profile.tenant else 'None'})")
            print(f"  Deleting {duplicates_to_delete.count()} duplicate(s):")
            for dup in duplicates_to_delete:
                print(f"    - Profile ID: {dup.id} (tenant: {dup.tenant.name if dup.tenant else 'None'})")
                dup.delete()
            print(f"  ✅ Cleaned up duplicates for {user.username}")
else:
    print("✅ No duplicate profiles found")

# Now check user 7 specifically
print("\n" + "="*60)
print("Checking user ID 7 specifically:")
try:
    user7 = User.objects.get(id=7)
    profiles = UserProfile.objects.filter(user=user7)
    print(f"User 7: {user7.username}")
    print(f"Profile count: {profiles.count()}")
    if profiles.exists():
        for p in profiles:
            print(f"  Profile ID: {p.id}, Tenant: {p.tenant.name if p.tenant else 'None'}")
except User.DoesNotExist:
    print("User 7 does not exist")

print("\n✅ Cleanup complete! You can now edit users in admin.")
