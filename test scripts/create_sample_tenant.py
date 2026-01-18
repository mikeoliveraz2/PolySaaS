#!/usr/bin/env python
"""
Script to create a sample tenant with branding information
"""
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant, Domain

def create_sample_tenant():
    """Create a sample tenant with branding"""
    try:
        # Check if tenant already exists
        tenant = Tenant.objects.filter(schema_name='demo').first()
        if tenant:
            print(f"Tenant '{tenant.name}' already exists")
            return tenant
        
        # Create new tenant
        tenant = Tenant.objects.create(
            schema_name='demo',
            name='Demo Corporation',
            tagline='Your Trusted ML Partner'
        )
        print(f"Created tenant: {tenant.name}")
        
        # Create domain for the tenant
        domain = Domain.objects.create(
            domain='localhost',  # For local development
            tenant=tenant,
            is_primary=True
        )
        print(f"Created domain: {domain.domain} for tenant: {tenant.name}")
        
        return tenant
        
    except Exception as e:
        print(f"Error creating tenant: {e}")
        return None

if __name__ == '__main__':
    tenant = create_sample_tenant()
    if tenant:
        print("\nSample tenant created successfully!")
        print(f"Name: {tenant.name}")
        print(f"Schema: {tenant.schema_name}")
        print(f"Tagline: {tenant.tagline}")
        print(f"Access admin at: http://localhost:8000/admin/")
    else:
        print("Failed to create tenant")
