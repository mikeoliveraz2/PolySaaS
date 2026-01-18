#!/usr/bin/env python
"""
Move NavigationItems from Public Tenant to Oliver Enterprises tenant
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import NavigationItem, NavigationPanel, Tenant

print("="*60)
print("Moving NavigationItems to Correct Tenant")
print("="*60)
print()

# Get tenants
public_tenant = Tenant.objects.filter(schema_name='public').first()
oliver_tenant = Tenant.objects.filter(name__icontains='oliver').first()

if not public_tenant or not oliver_tenant:
    print("ERROR: Could not find tenants!")
    exit(1)

print(f"Public Tenant: {public_tenant.name}")
print(f"Oliver Enterprises: {oliver_tenant.name}")
print()

# Get items in Public Tenant that should be in Oliver Enterprises
public_panel = NavigationPanel.objects.filter(tenant=public_tenant, title__icontains='External Services').first()
oliver_panel = NavigationPanel.objects.filter(tenant=oliver_tenant, title__icontains='External Services').first()

if not public_panel:
    print("ERROR: Public Tenant External Services panel not found!")
    exit(1)

# Ensure Oliver Enterprises has an External Services panel
if not oliver_panel:
    print("Creating External Services panel in Oliver Enterprises...")
    oliver_panel = NavigationPanel.objects.create(
        tenant=oliver_tenant,
        title='External Services',
        panel_type='integrations',
        description='External service integrations',
        is_active=True,
        sort_order=100
    )
    print(f"Created panel: {oliver_panel.title}")
else:
    print(f"Found existing panel: {oliver_panel.title}")

print()

# Get items in public panel
public_items = NavigationItem.objects.filter(panel=public_panel)
print(f"Items in Public Tenant panel: {public_items.count()}")

# Items that should be moved (Notion, Airtable, OsTicket)
items_to_move = ['Notion', 'Airtable', 'OsTicket']

moved_count = 0
for item in public_items:
    if item.title in items_to_move:
        print(f"\nMoving '{item.title}' from Public Tenant to Oliver Enterprises...")

        # Check if item already exists in Oliver panel
        existing = NavigationItem.objects.filter(panel=oliver_panel, title=item.title).first()
        if existing:
            print(f"  Item '{item.title}' already exists in Oliver Enterprises. Skipping.")
        else:
            # Create new item in Oliver panel
            new_item = NavigationItem.objects.create(
                panel=oliver_panel,
                title=item.title,
                item_type=item.item_type,
                url=item.url,
                description=item.description,
                icon_style=item.icon_style,
                icon_value=item.icon_value,
                target=item.target,
                requires_authentication=item.requires_authentication,
                requires_permissions=item.requires_permissions,
                is_active=item.is_active,
                sort_order=item.sort_order,
                item_css_class=item.item_css_class,
                button_color=item.button_color
            )
            print(f"  Created '{new_item.title}' in Oliver Enterprises panel")
            moved_count += 1

            # Optionally delete the public tenant item
            # Uncomment if you want to remove from public tenant
            # item.delete()
            # print(f"  Deleted '{item.title}' from Public Tenant")

print()
print("="*60)
print(f"Summary: Moved {moved_count} items to Oliver Enterprises")
print("="*60)

# Show final state
oliver_items = NavigationItem.objects.filter(panel=oliver_panel)
print(f"\nOliver Enterprises now has {oliver_items.count()} items:")
for item in oliver_items:
    print(f"  - {item.title}")

