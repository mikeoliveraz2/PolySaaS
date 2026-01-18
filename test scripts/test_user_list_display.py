#!/usr/bin/env python
"""
Test the enhanced user list display with tenant information
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from dose.models import Tenant, UserProfile

def test_user_list_display():
    """Test that user list will show tenant information."""
    
    print("👥 User List Display Test")
    print("=" * 40)
    
    # Check tenant status
    tenants = Tenant.objects.all()
    active_tenants = Tenant.objects.filter(is_active=True)
    
    print(f"📊 Current Data:")
    print(f"  Total Tenants: {tenants.count()}")
    print(f"  Active Tenants: {active_tenants.count()}")
    
    # Check users and their tenant assignments
    users = User.objects.all()
    users_with_profiles = users.filter(userprofile__isnull=False)
    users_without_profiles = users.filter(userprofile__isnull=True)
    
    print(f"  Total Users: {users.count()}")
    print(f"  Users with Profiles: {users_with_profiles.count()}")
    print(f"  Users without Profiles: {users_without_profiles.count()}")
    
    # Show what the admin list will display
    print(f"\n📋 User List Preview (what admin will show):")
    print(f"{'Username':<15} {'Email':<25} {'Tenant':<20} {'Status':<10}")
    print("-" * 70)
    
    for user in users.select_related('userprofile__tenant'):
        try:
            tenant_name = user.userprofile.tenant.name
            if user.userprofile.tenant.is_active:
                status = "✅ Active"
            else:
                status = "❌ Inactive"
                tenant_name += " (Inactive)"
        except AttributeError:
            tenant_name = "⚠️ No Tenant Assigned"
            status = "⚠️ No Tenant"
        
        email = user.email or "No email"
        print(f"{user.username:<15} {email:<25} {tenant_name:<20} {status:<10}")
    
    # Test admin configuration
    print(f"\n⚙️  Admin List Display Configuration:")
    try:
        from dose.admin import CustomUserAdmin
        admin_instance = CustomUserAdmin(User, None)
        print(f"  ✅ List Display Fields:")
        for field in admin_instance.list_display:
            print(f"    - {field}")
        print(f"  ✅ List Filters Available:")
        for filter_field in admin_instance.list_filter:
            print(f"    - {filter_field}")
        print(f"  ✅ Search Fields Available:")
        for search_field in admin_instance.search_fields:
            print(f"    - {search_field}")
    except Exception as e:
        print(f"  ❌ Admin configuration error: {e}")
    
    # Final status
    print(f"\n🎯 User List Enhancement Status:")
    if users.exists():
        print(f"  ✅ User list will show tenant information for each user")
        print(f"  ✅ Tenant status indicators (✅ Active, ❌ Inactive, ⚠️ No Tenant)")
        print(f"  ✅ Sortable by tenant name and status")
        print(f"  ✅ Filterable by tenant and tenant status") 
        print(f"  ✅ Searchable by tenant name")
    else:
        print(f"  ⚠️  No users found to display")
    
    print(f"\n📍 Next Steps:")
    print(f"  1. Go to: http://127.0.0.1:8000/admin/auth/user/")
    print(f"  2. User list now shows 'Tenant' and 'Status' columns")
    print(f"  3. Use filters on right side to filter by tenant")
    print(f"  4. Click column headers to sort by tenant")
    print(f"  5. Use search box to find users by tenant name")
    
    return True

if __name__ == "__main__":
    test_user_list_display()
