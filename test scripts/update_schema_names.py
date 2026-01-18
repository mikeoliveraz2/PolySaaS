#!/usr/bin/env python
"""
Update existing tenants with schema names
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant

def update_tenant_schema_names():
    """Update existing tenants with schema names based on their slugs."""
    
    print("🏥 Updating Tenant Schema Names")
    print("=" * 40)
    
    # Get all tenants
    tenants = Tenant.objects.all()
    
    if not tenants.exists():
        print("No tenants found. Creating a sample tenant...")
        tenant = Tenant.objects.create(
            name="Medical Center A",
            slug="medical-center-a",
            description="Sample medical center",
            is_active=True
        )
        print(f"✅ Created tenant: {tenant.name}")
        tenants = [tenant]
    
    print(f"📊 Found {tenants.count()} tenants")
    
    # Update tenants with schema names
    updated_count = 0
    for tenant in tenants:
        old_schema = getattr(tenant, 'schema_name', None)
        
        if not tenant.schema_name and tenant.slug:
            # Generate schema name from slug
            tenant.schema_name = tenant.slug.replace('-', '_').lower()
            tenant.save()
            print(f"✅ Updated '{tenant.name}': slug='{tenant.slug}' → schema='{tenant.schema_name}'")
            updated_count += 1
        elif tenant.schema_name:
            print(f"ℹ️  '{tenant.name}' already has schema: '{tenant.schema_name}'")
        else:
            print(f"⚠️  '{tenant.name}' has no slug to generate schema name from")
    
    print(f"\n📋 Schema Name Status:")
    print(f"{'Name':<20} {'Slug':<20} {'Schema Name':<20}")
    print("-" * 62)
    
    for tenant in Tenant.objects.all():
        schema_name = tenant.schema_name or "None"
        slug = tenant.slug or "None"
        print(f"{tenant.name:<20} {slug:<20} {schema_name:<20}")
    
    print(f"\n✅ Updated {updated_count} tenants with schema names")
    print("🎯 Tenant list should now show proper schema names instead of N/A!")
    
    return True

if __name__ == "__main__":
    update_tenant_schema_names()
