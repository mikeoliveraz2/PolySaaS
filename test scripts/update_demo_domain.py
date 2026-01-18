#!/usr/bin/env python
"""
Script to update demo tenant domain to use localhost with port
"""
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant, Domain

def update_demo_domain():
    """Update demo tenant to use localhost:8001"""
    try:
        # Get the demo tenant
        tenant = Tenant.objects.filter(schema_name='demo').first()
        if not tenant:
            print("No demo tenant found")
            return None
        
        # Remove old domain
        Domain.objects.filter(tenant=tenant).delete()
        
        # Create new domain using different port
        domain = Domain.objects.create(
            domain='localhost:8001',  # Use different port
            tenant=tenant,
            is_primary=True
        )
        
        print(f"Updated domain for {tenant.name}: {domain.domain}")
        return domain
        
    except Exception as e:
        print(f"Error updating domain: {e}")
        return None

if __name__ == '__main__':
    domain = update_demo_domain()
    if domain:
        print(f"\nDemo tenant now accessible at: http://{domain.domain}/admin/")
        print("You can also start a second server on port 8001:")
        print("python manage.py runserver 8001")
    else:
        print("Failed to update domain")
