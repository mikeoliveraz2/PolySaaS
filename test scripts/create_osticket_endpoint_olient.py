#!/usr/bin/env python
"""
Create OS Ticket PassThroughEndpoint in the olient (Oliver Enterprise) schema
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import PassThroughEndpoint, Tenant

print("\n" + "="*100)
print("CREATING OS TICKET ENDPOINT IN OLIENT SCHEMA")
print("="*100 + "\n")

# Get the olient tenant
olient_tenant = Tenant.objects.filter(schema_name='olient').first()
if not olient_tenant:
    print("❌ ERROR: 'olient' tenant not found!")
    print("Available tenants:")
    for t in Tenant.objects.all():
        print(f"  - {t.name} (schema: {t.schema_name})")
    sys.exit(1)

print(f"✓ Found tenant: {olient_tenant.name} (schema: {olient_tenant.schema_name})\n")

# Switch to olient schema
with connection.cursor() as cursor:
    cursor.execute("SET search_path TO olient,public;")
    print("✓ Switched to olient schema\n")

    # Check if OS Ticket endpoint already exists
    existing = PassThroughEndpoint.objects.filter(
        trigger_path__icontains='osticket'
    ).first()

    if existing:
        print(f"⚠ OS Ticket endpoint already exists in olient schema:")
        print(f"  ID: {existing.id}")
        print(f"  Trigger Path: {existing.trigger_path}")
        print(f"  Endpoint URL: {existing.endpoint_url}")
        print(f"  Is Enabled: {existing.is_enabled}")
        print()

        # Update it to point to polysaas
        existing.endpoint_url = "https://polysaas.supportsystem.com/scp/"
        existing.trigger_path = "osticket"
        existing.is_enabled = True
        existing.save()
        print(f"✓ Updated endpoint to point to polysaas.supportsystem.com")
    else:
        # Create new endpoint
        endpoint = PassThroughEndpoint.objects.create(
            trigger_path='osticket',
            endpoint_url='https://polysaas.supportsystem.com/scp/',
            passthrough_type='scraper',
            provider='custom',
            is_enabled=True,
            bypass_middleware=False,
            show_in_menu=True,
            description='OS Ticket support system for Oliver Enterprise',
        )

        print(f"✓ Created new OS Ticket endpoint in olient schema:")
        print(f"  ID: {endpoint.id}")
        print(f"  Trigger Path: {endpoint.trigger_path}")
        print(f"  Endpoint URL: {endpoint.endpoint_url}")
        print(f"  Passthrough Type: {endpoint.passthrough_type}")
        print(f"  Is Enabled: {endpoint.is_enabled}")
        print()

    # Reset search_path
    cursor.execute("SET search_path TO public;")
    print("✓ Reset search_path to public\n")

print("="*100)
print("NEXT STEPS:")
print("="*100)
print("1. Make sure you're logged in as a user in the olient tenant")
print("2. Go to Django admin → PassThrough Endpoints")
print("3. You should see the OS Ticket endpoint in the olient schema")
print("4. Set 'Auth Username' and 'Auth Password' for the endpoint")
print("5. Click 'Auto-Login (Playwright)' button")
print("="*100)

