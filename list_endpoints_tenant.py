#!/usr/bin/env python
import os
import sys
import django

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint, Tenant
from django.db import connection

def set_schema(schema_name):
    """Set the PostgreSQL search_path to the specified schema"""
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO {schema_name},public;')

# Get olient tenant
tenant = Tenant.objects.using('default').filter(schema_name='olient').first()
if not tenant:
    print("ERROR: olient tenant not found")
    sys.exit(1)

print(f"Switching to tenant: {tenant.schema_name}")
set_schema(tenant.schema_name)

# Query PassThroughEndpoints
pts = PassThroughEndpoint.objects.all().order_by('menu_sort_order', 'menu_title')
print(f"\nTotal endpoints in {tenant.schema_name}: {pts.count()}\n")

for i, pt in enumerate(pts, 1):
    print(f"{i}. Menu: '{pt.menu_title}'")
    print(f"   Trigger: {pt.trigger_path}")
    print(f"   URL: {pt.endpoint_url}")
    print(f"   Enabled: {pt.is_enabled}, Show in menu: {pt.show_in_menu}")
    print()
