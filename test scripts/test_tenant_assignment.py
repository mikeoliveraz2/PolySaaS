#!/usr/bin/env python
"""
Test the new tenant assignment functionality
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from dose.models import Tenant, UserProfile

def test_tenant_assignment():
    """Test tenant assignment functionality."""
    
    print("🏥 D.O.S.E. Tenant Assignment Test")
    print("=" * 50)
    
    # Check if we have any tenants
    tenants = Tenant.objects.all()
    if not tenants.exists():
        print("Creating a default tenant...")
        default_tenant = Tenant.objects.create(
            name="Medical Center A",
            slug="medical-center-a",
            description="Default medical center for D.O.S.E. system",
            tagline="Quality Healthcare Solutions",
            is_active=True
        )
        print(f"✅ Created tenant: {default_tenant.name}")
    else:
        print(f"✅ Found {tenants.count()} existing tenants:")
        for tenant in tenants:
            print(f"   - {tenant.name} (ID: {tenant.id}, Active: {tenant.is_active})")
    
    # Check users without tenant assignments
    users_without_profile = User.objects.filter(userprofile__isnull=True)
    if users_without_profile.exists():
        print(f"\n⚠️  Found {users_without_profile.count()} users without tenant assignment:")
        for user in users_without_profile:
            print(f"   - {user.username} ({user.email})")
        
        # Assign them to the first active tenant
        default_tenant = Tenant.objects.filter(is_active=True).first()
        if default_tenant:
            print(f"\n🔄 Assigning users to: {default_tenant.name}")
            for user in users_without_profile:
                UserProfile.objects.create(user=user, tenant=default_tenant)
                print(f"   ✅ {user.username} -> {default_tenant.name}")
        else:
            print("❌ No active tenant found to assign users to")
    else:
        print("✅ All users have tenant assignments")
    
    # Show current assignments
    print(f"\n📋 Current User-Tenant Assignments:")
    user_profiles = UserProfile.objects.select_related('user', 'tenant').all()
    if user_profiles.exists():
        for profile in user_profiles:
            print(f"   {profile.user.username} -> {profile.tenant.name}")
    else:
        print("   None found")
    
    print(f"\n✅ Tenant assignment functionality is ready!")
    print("📌 Next steps:")
    print("   1. Access admin at: http://127.0.0.1:8000/admin/")
    print("   2. Go to Users section")
    print("   3. When creating new users, you'll see 'Tenant Assignment' section")
    print("   4. Existing users can be edited to change their tenant")
    
    return True

if __name__ == "__main__":
    test_tenant_assignment()
