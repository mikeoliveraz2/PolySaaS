#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant, Domain

try:
    # Create demo tenant
    tenant = Tenant.objects.create(
        name='Demo Company',
        schema_name='demo',
        tagline='Your Partner in Digital Excellence'
    )
    
    # Create domain
    domain = Domain.objects.create(
        domain='demo.localhost',
        tenant=tenant,
        is_primary=True
    )
    
    print(f'Demo tenant created: {tenant.name}')
    print(f'Domain: {domain.domain}')
    print('You can now access the admin and upload a logo!')
    
except Exception as e:
    print(f'Error creating demo tenant: {e}')
