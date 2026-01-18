"""
Fix tenant constraint issue for UserProfile model
1. Create a default public tenant if none exists
2. Update the signal handler to assign default tenant to new users
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant, UserProfile
from django.contrib.auth.models import User

def create_default_tenant():
    """Create a default public tenant if none exists"""
    public_tenant, created = Tenant.objects.get_or_create(
        slug='public',
        defaults={
            'name': 'Public Tenant',
            'description': 'Default tenant for all users',
            'is_active': True
        }
    )
    if created:
        print(f"✅ Created default public tenant: {public_tenant}")
    else:
        print(f"✅ Public tenant already exists: {public_tenant}")
    
    return public_tenant

def fix_existing_userprofiles(default_tenant):
    """Update existing UserProfiles that have null tenant_id"""
    null_profiles = UserProfile.objects.filter(tenant__isnull=True)
    count = null_profiles.count()
    
    if count > 0:
        print(f"Found {count} UserProfile records with null tenant_id")
        null_profiles.update(tenant=default_tenant)
        print(f"✅ Updated {count} UserProfile records to use default tenant")
    else:
        print("✅ No UserProfile records with null tenant_id found")

def main():
    print("🔧 Fixing tenant constraint issue...")
    
    # 1. Create default tenant
    default_tenant = create_default_tenant()
    
    # 2. Fix existing UserProfiles
    fix_existing_userprofiles(default_tenant)
    
    print("\n✅ Tenant constraint fix completed!")
    print(f"Default tenant ID: {default_tenant.id}")
    print("Now you need to update the signal handler in dose/signals.py")

if __name__ == "__main__":
    main()