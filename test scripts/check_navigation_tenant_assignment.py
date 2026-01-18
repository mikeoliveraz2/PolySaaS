#!/usr/bin/env python
"""
Check NavigationItems tenant assignment
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import NavigationItem, NavigationPanel, Tenant
from django.contrib.auth.models import User

print("="*60)
print("NavigationItems Tenant Assignment Check")
print("="*60)
print()

# Get all tenants
tenants = Tenant.objects.all()
print(f"Tenants: {tenants.count()}")
for tenant in tenants:
    print(f"  - {tenant.name} (schema: {tenant.schema_name})")
print()

# Check NavigationItems by tenant
for tenant in tenants:
    panels = NavigationPanel.objects.filter(tenant=tenant)
    items = NavigationItem.objects.filter(panel__tenant=tenant)

    print(f"{tenant.name} ({tenant.schema_name}):")
    print(f"  Panels: {panels.count()}")
    for panel in panels:
        panel_items = NavigationItem.objects.filter(panel=panel)
        print(f"    - {panel.title}: {panel_items.count()} items")
        for item in panel_items:
            print(f"        - {item.title} (Active: {item.is_active})")
    print(f"  Total Items: {items.count()}")
    print()

# Check for items that might be orphaned or mis-assigned
all_items = NavigationItem.objects.all()
print("="*60)
print("All NavigationItems Summary:")
print("="*60)
for item in all_items:
    tenant_name = item.panel.tenant.name if item.panel and item.panel.tenant else "NO TENANT"
    print(f"  {item.title} -> Panel: {item.panel.title if item.panel else 'NO PANEL'} -> Tenant: {tenant_name}")

print()
print("="*60)
print("Checking for items that should be in Oliver Enterprises:")
print("="*60)

oliver_tenant = Tenant.objects.filter(name__icontains='oliver').first()
if oliver_tenant:
    print(f"Oliver Enterprises tenant: {oliver_tenant.name} (schema: {oliver_tenant.schema_name})")
    oliver_items = NavigationItem.objects.filter(panel__tenant=oliver_tenant)
    print(f"Items in Oliver Enterprises: {oliver_items.count()}")
    for item in oliver_items:
        print(f"  - {item.title} (Panel: {item.panel.title})")

    # Check public tenant items
    public_tenant = Tenant.objects.filter(schema_name='public').first()
    if public_tenant:
        public_items = NavigationItem.objects.filter(panel__tenant=public_tenant)
        print(f"\nItems in Public Tenant: {public_items.count()}")
        for item in public_items:
            print(f"  - {item.title} (Panel: {item.panel.title})")
            print(f"    This item might belong to Oliver Enterprises!")

