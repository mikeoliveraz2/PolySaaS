#!/usr/bin/env python
"""
Remove NavigationItems from Public Tenant that were moved to Oliver Enterprises
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import NavigationItem, NavigationPanel, Tenant

print("="*60)
print("Cleaning Up Public Tenant Items")
print("="*60)
print()

# Get tenants
public_tenant = Tenant.objects.filter(schema_name='public').first()
oliver_tenant = Tenant.objects.filter(name__icontains='oliver').first()

# Get panels
public_panel = NavigationPanel.objects.filter(tenant=public_tenant, title__icontains='External Services').first()
oliver_panel = NavigationPanel.objects.filter(tenant=oliver_tenant, title__icontains='External Services').first()

if not public_panel or not oliver_panel:
    print("ERROR: Panels not found!")
    exit(1)

# Items that were moved
items_to_remove = ['Notion', 'Airtable', 'OsTicket']

print("Removing items from Public Tenant that were moved to Oliver Enterprises:")
for item_title in items_to_remove:
    item = NavigationItem.objects.filter(panel=public_panel, title=item_title).first()
    if item:
        print(f"  Deleting '{item.title}' from Public Tenant...")
        item.delete()
        print(f"    Deleted")
    else:
        print(f"  '{item_title}' not found in Public Tenant")

print()
print("="*60)
print("Final State:")
print("="*60)

public_items = NavigationItem.objects.filter(panel=public_panel)
oliver_items = NavigationItem.objects.filter(panel=oliver_panel)

print(f"Public Tenant: {public_items.count()} items")
for item in public_items:
    print(f"  - {item.title}")

print()
print(f"Oliver Enterprises: {oliver_items.count()} items")
for item in oliver_items:
    print(f"  - {item.title}")

