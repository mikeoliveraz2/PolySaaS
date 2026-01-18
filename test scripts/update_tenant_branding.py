#!/usr/bin/env python
"""
Script to update tenant with better branding information
"""
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant

def update_tenant_branding():
    """Update tenant with better branding"""
    try:
        # Get the demo tenant
        tenant = Tenant.objects.filter(schema_name='demo').first()
        if not tenant:
            print("No demo tenant found")
            return None
        
        # Update tenant branding
        tenant.name = 'Dose AI Corporation'
        tenant.tagline = 'Advanced Machine Learning & Workflow Management'
        tenant.save()
        
        print(f"Updated tenant: {tenant.name}")
        print(f"New tagline: {tenant.tagline}")
        
        return tenant
        
    except Exception as e:
        print(f"Error updating tenant: {e}")
        return None

if __name__ == '__main__':
    tenant = update_tenant_branding()
    if tenant:
        print("\nTenant branding updated successfully!")
        print("Now refresh http://localhost:8000/admin/dose/tenant/ to see the changes")
    else:
        print("Failed to update tenant")
