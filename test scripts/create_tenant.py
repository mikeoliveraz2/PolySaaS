#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant, Domain

# Create a public tenant (required for django-tenants)
tenant = Tenant(schema_name='public', name='Public')
tenant.save()

# Create domain for the public tenant  
domain = Domain()
domain.domain = 'localhost'
domain.tenant = tenant
domain.is_primary = True
domain.save()

print("Public tenant created successfully!")

# Now create a demo company tenant
demo_tenant = Tenant(schema_name='demo', name='Demo Company')
demo_tenant.tagline = 'Your Partner in Digital Excellence'
demo_tenant.save()

# Create domain for demo tenant
demo_domain = Domain()
demo_domain.domain = 'demo.localhost'
demo_domain.tenant = demo_tenant
demo_domain.is_primary = True
demo_domain.save()

print("Demo tenant created successfully!")
