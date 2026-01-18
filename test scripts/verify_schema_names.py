#!/usr/bin/env python
"""
Verify that schema names are now showing in tenant admin
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant

def verify_schema_names():
    """Verify that tenants have proper schema names."""
    
    print("🔍 Schema Name Verification")
    print("=" * 40)
    
    # Check all tenants
    tenants = Tenant.objects.all()
    
    if not tenants.exists():
        print("⚠️  No tenants found in database")
        return False
    
    print(f"📊 Checking {tenants.count()} tenants...")
    
    all_good = True
    print(f"\n📋 Tenant Schema Status:")
    print(f"{'Name':<25} {'Slug':<20} {'Schema Name':<20} {'Status':<10}")
    print("-" * 77)
    
    for tenant in tenants:
        if hasattr(tenant, 'schema_name') and tenant.schema_name:
            status = "✅ Good"
        else:
            status = "❌ Missing"
            all_good = False
        
        name = tenant.name[:24] if len(tenant.name) > 24 else tenant.name
        slug = tenant.slug[:19] if tenant.slug and len(tenant.slug) > 19 else (tenant.slug or "None")
        schema = getattr(tenant, 'schema_name', None)
        schema = schema[:19] if schema and len(schema) > 19 else (schema or "None")
        
        print(f"{name:<25} {slug:<20} {schema:<20} {status:<10}")
    
    # Test admin display methods
    print(f"\n⚙️  Admin Configuration Test:")
    try:
        from dose.admin import TenantAdmin
        from django.contrib.admin.sites import AdminSite
        
        admin_site = AdminSite()
        admin_instance = TenantAdmin(Tenant, admin_site)
        
        print(f"  List Display Fields: {admin_instance.list_display}")
        
        if tenants.exists():
            sample_tenant = tenants.first()
            print(f"\n  Testing on '{sample_tenant.name}':")
            
            # Test direct field access
            schema_name = getattr(sample_tenant, 'schema_name', 'N/A')
            print(f"    Direct schema_name: '{schema_name}'")
            
            # Test admin methods
            user_count = admin_instance.get_user_count(sample_tenant)
            print(f"    User count method: '{user_count}'")
            
    except Exception as e:
        print(f"  ❌ Admin test error: {e}")
        all_good = False
    
    print(f"\n🎯 Final Status:")
    if all_good:
        print(f"  ✅ All tenants have schema names - should show in admin!")
        print(f"  ✅ No more N/A values expected")
    else:
        print(f"  ⚠️  Some tenants missing schema names")
        print(f"  💡 Run: python update_schema_names.py")
    
    print(f"\n📍 Check Admin Interface:")
    print(f"  1. Go to: http://127.0.0.1:8000/admin/dose/tenant/")
    print(f"  2. Schema Name column should show actual values")
    print(f"  3. No more 'N/A' values should appear")
    
    return all_good

if __name__ == "__main__":
    verify_schema_names()
