#!/usr/bin/env python
"""
Script to list all tenants and their branding information
"""
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant, Domain

def list_tenants():
    """List all tenants and their information"""
    try:
        tenants = Tenant.objects.all()
        print(f"Found {tenants.count()} tenant(s):")
        print("-" * 50)
        
        for tenant in tenants:
            print(f"Name: {tenant.name}")
            print(f"Schema: {tenant.schema_name}")
            print(f"Tagline: {tenant.tagline}")
            print(f"Created: {tenant.created_on}")
            
            # Show domains
            domains = Domain.objects.filter(tenant=tenant)
            print(f"Domains: {', '.join([d.domain for d in domains])}")
            print("-" * 50)
        
        return tenants
        
    except Exception as e:
        print(f"Error listing tenants: {e}")
        return None

if __name__ == '__main__':
    tenants = list_tenants()
    if tenants and tenants.count() > 0:
        print(f"\nTenants are available in the database.")
        print("You should now see them at: http://localhost:8000/admin/dose/tenant/")
    else:
        print("No tenants found in database")
