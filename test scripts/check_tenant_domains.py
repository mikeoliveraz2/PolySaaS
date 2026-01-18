#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant, Domain

print("=== CHECKING TENANT-DOMAIN RELATIONSHIPS ===")

# List all tenants
print("\nAll Tenants:")
for tenant in Tenant.objects.all():
    print(f"  - Schema: {tenant.schema_name}, Name: {tenant.name}, Tagline: {tenant.tagline}")

# List all domains
print("\nAll Domains:")
for domain in Domain.objects.all():
    print(f"  - Domain: {domain.domain}, Tenant: {domain.tenant.name} ({domain.tenant.schema_name}), Primary: {domain.is_primary}")

# Check specifically for demo.localhost
print("\nChecking demo.localhost:")
try:
    demo_domain = Domain.objects.get(domain='demo.localhost')
    print(f"  - Found: {demo_domain.domain} -> {demo_domain.tenant.name} ({demo_domain.tenant.schema_name})")
except Domain.DoesNotExist:
    print("  - demo.localhost domain not found!")

# Check for any domains containing 'localhost'
print("\nAll localhost domains:")
localhost_domains = Domain.objects.filter(domain__contains='localhost')
for domain in localhost_domains:
    print(f"  - {domain.domain} -> {domain.tenant.name} ({domain.tenant.schema_name}), Primary: {domain.is_primary}")

print("\n=== FIXING DOMAIN ASSIGNMENT ===")

# Ensure demo.localhost points to the right tenant
demo_tenant = Tenant.objects.get(schema_name='demo')
demo_domain, created = Domain.objects.get_or_create(
    domain='demo.localhost',
    defaults={'tenant': demo_tenant, 'is_primary': True}
)

if not created:
    # Update existing domain to point to demo tenant
    demo_domain.tenant = demo_tenant
    demo_domain.save()
    print(f"✓ Updated demo.localhost to point to {demo_tenant.name}")
else:
    print(f"✓ Created demo.localhost pointing to {demo_tenant.name}")

print(f"\nFinal check: demo.localhost -> {demo_domain.tenant.name} ({demo_domain.tenant.schema_name})")
