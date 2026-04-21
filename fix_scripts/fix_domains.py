#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant, Domain
from django.db import connection

# Set schema to public
connection.set_schema_to_public()

print("Current tenants and domains:")
tenants = Tenant.objects.all()
for tenant in tenants:
    print(f"\nTenant: {tenant.name} (schema: {tenant.schema_name})")
    domains = Domain.objects.filter(tenant=tenant)
    for domain in domains:
        print(f"  Domain: {domain.domain} (primary: {domain.is_primary})")

# Make sure localhost points to public tenant
try:
    public_tenant = Tenant.objects.get(schema_name='public')
    
    # Update or create localhost domain for public tenant
    domain, created = Domain.objects.get_or_create(
        domain='localhost',
        defaults={'tenant': public_tenant, 'is_primary': True}
    )
    if not created:
        domain.tenant = public_tenant
        domain.is_primary = True
        domain.save()
    
    print(f"\nFixed localhost domain -> {public_tenant.name}")
    
    # Also add 127.0.0.1 domain
    domain127, created = Domain.objects.get_or_create(
        domain='127.0.0.1',
        defaults={'tenant': public_tenant, 'is_primary': False}
    )
    if not created:
        domain127.tenant = public_tenant
        domain127.save()
    
    print(f"Fixed 127.0.0.1 domain -> {public_tenant.name}")
    
except Exception as e:
    print(f"Error: {e}")

print("\nFinal domain configuration:")
domains = Domain.objects.all()
for domain in domains:
    print(f"  {domain.domain} -> {domain.tenant.name} (primary: {domain.is_primary})")
