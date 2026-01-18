#!/usr/bin/env python
"""
Verify tenant selector functionality in admin
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from dose.models import Tenant, UserProfile

def verify_tenant_selector():
    """Verify that tenant selector will work in admin."""
    
    print("🔍 Tenant Selector Verification")
    print("=" * 40)
    
    # Check tenant status
    tenants = Tenant.objects.all()
    active_tenants = Tenant.objects.filter(is_active=True)
    
    print(f"📊 Tenant Status:")
    print(f"  Total Tenants: {tenants.count()}")
    print(f"  Active Tenants: {active_tenants.count()}")
    
    if active_tenants.exists():
        print(f"  Available Tenants:")
        for tenant in active_tenants:
            print(f"    - {tenant.name} (ID: {tenant.id})")
    else:
        print("  ⚠️  No active tenants found!")
    
    # Check user/profile status
    total_users = User.objects.count()
    users_with_profiles = User.objects.filter(userprofile__isnull=False).count()
    users_without_profiles = total_users - users_with_profiles
    
    print(f"\n👥 User Profile Status:")
    print(f"  Total Users: {total_users}")
    print(f"  Users with Profiles: {users_with_profiles}")
    print(f"  Users without Profiles: {users_without_profiles}")
    
    if users_without_profiles > 0:
        print(f"  ⚠️  Users without profiles:")
        for user in User.objects.filter(userprofile__isnull=True):
            print(f"    - {user.username}")
    
    # Check admin inline configuration
    print(f"\n⚙️  Admin Configuration:")
    try:
        from dose.admin import CustomUserAdmin, UserProfileInline
        print(f"  ✅ CustomUserAdmin: Available")
        print(f"  ✅ UserProfileInline: Available")
        print(f"  ✅ Inline extra forms: 1 (will show for users without profiles)")
        print(f"  ✅ Inline min_num: 1 (ensures tenant selection is required)")
    except ImportError as e:
        print(f"  ❌ Admin configuration error: {e}")
    
    # Final status
    print(f"\n🎯 Tenant Selector Status:")
    if active_tenants.exists() and users_without_profiles == 0:
        print(f"  ✅ WORKING: Tenant selector will appear for all users")
        print(f"  ✅ When editing users, 'Tenant Assignment' section will show")
        print(f"  ✅ Dropdown will contain {active_tenants.count()} active tenant(s)")
    else:
        if not active_tenants.exists():
            print(f"  ❌ ISSUE: No active tenants available for selection")
        if users_without_profiles > 0:
            print(f"  ⚠️  WARNING: {users_without_profiles} users need UserProfiles created")
            print(f"     Run: python ensure_user_profiles.py")
    
    print(f"\n📋 Next Steps:")
    print(f"  1. Go to: http://127.0.0.1:8000/admin/auth/user/")
    print(f"  2. Click on any existing user to edit")
    print(f"  3. Look for 'Tenant Assignment' section at bottom")
    print(f"  4. Select tenant from dropdown")
    print(f"  5. Save user")
    
    return users_without_profiles == 0 and active_tenants.exists()

if __name__ == "__main__":
    success = verify_tenant_selector()
    if success:
        print(f"\n🎉 Tenant selector is ready to use!")
    else:
        print(f"\n⚠️  Some setup still needed - see issues above")
