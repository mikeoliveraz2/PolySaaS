#!/usr/bin/env python
"""
Ensure all users have UserProfiles so tenant selector appears in admin
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from dose.models import Tenant, UserProfile

def ensure_user_profiles():
    """Ensure all users have UserProfiles."""
    
    print("🏥 D.O.S.E. UserProfile Sync")
    print("=" * 40)
    
    # Check if we have any tenants, create one if not
    if not Tenant.objects.exists():
        print("Creating default tenant...")
        default_tenant = Tenant.objects.create(
            name="Medical Center",
            slug="medical-center",
            description="Default medical center",
            is_active=True
        )
        print(f"✅ Created tenant: {default_tenant.name}")
    
    # Get default tenant
    default_tenant = Tenant.objects.filter(is_active=True).first()
    
    # Find users without UserProfiles
    users_without_profile = User.objects.filter(userprofile__isnull=True)
    
    if users_without_profile.exists():
        print(f"Found {users_without_profile.count()} users without UserProfile:")
        for user in users_without_profile:
            print(f"  - {user.username}")
            UserProfile.objects.create(user=user, tenant=default_tenant)
            print(f"    ✅ Created UserProfile for {user.username} -> {default_tenant.name}")
    else:
        print("✅ All users already have UserProfiles")
    
    # Show current status
    print(f"\n📊 Current Status:")
    print(f"  Total Users: {User.objects.count()}")
    print(f"  Users with Profiles: {UserProfile.objects.count()}")
    print(f"  Active Tenants: {Tenant.objects.filter(is_active=True).count()}")
    
    print(f"\n🎉 All users now have UserProfiles!")
    print(f"✅ Tenant selector will now appear when editing users in admin")
    
    return True

if __name__ == "__main__":
    ensure_user_profiles()
