#!/usr/bin/env python
"""
Add /dose/osticket/ PassThroughEndpoint to database for all tenants
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint, Tenant

# Get all tenants
tenants = Tenant.objects.all()
print(f"\n📝 Found {tenants.count()} tenants\n")

for tenant in tenants:
    # Check if endpoint already exists
    existing = PassThroughEndpoint.objects.filter(
        tenant=tenant,
        trigger_path__iexact='/dose/osticket/'
    ).first()

    if existing:
        print(f"✅ {tenant.name}: /dose/osticket/ already configured")
        continue

    # Create endpoint
    endpoint = PassThroughEndpoint.objects.create(
        tenant=tenant,
        trigger_path='/dose/osticket/',
        endpoint_url='http://localhost:8001',
        is_enabled=True,
        name='OSTicket (HOME)',
        description='OSTicket passthrough for HOME sidebar (/dose/osticket/)'
    )
    print(f"✅ {tenant.name}: Created /dose/osticket/ → http://localhost:8001")

print("\n✨ Done! Now try: http://localhost:8000/dose/osticket/\n")
