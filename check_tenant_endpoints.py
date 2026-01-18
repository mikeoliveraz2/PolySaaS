#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint, Tenant
from django.db import connection

# Get olient tenant
tenant = Tenant.objects.using('default').filter(schema_name='olient').first()
if not tenant:
    print("ERROR: olient tenant not found")
    exit(1)

print(f"Switching to tenant: {tenant.schema_name}")
connection.set_tenant(tenant)

# Query PassThroughEndpoints
pts = PassThroughEndpoint.objects.all()
print(f"\nTotal endpoints in {tenant.schema_name}: {pts.count()}\n")

for i, pt in enumerate(pts, 1):
    print(f"{i}. Menu: '{pt.menu_title}'")
    print(f"   Trigger: {pt.trigger_path}")
    print(f"   URL: {pt.endpoint_url}")
    print(f"   Enabled: {pt.is_enabled}")
    print(f"   Show in menu: {pt.show_in_menu}")
    print()
