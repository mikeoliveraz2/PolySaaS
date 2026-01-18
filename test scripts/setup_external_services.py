#!/usr/bin/env python
"""
Setup script to add Notion and Airtable as external services in the sidebar.
These will open in new windows and can be explained as "passthrough in progress".
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import NavigationPanel, NavigationItem
from dose.utils import get_current_tenant
from django.contrib.auth.models import User

def setup_external_services():
    """Create or update External Services panel with Notion and Airtable"""

    # Get the first tenant (or create a default one)
    # In production, you'd want to get the current tenant from request
    from dose.models import Tenant
    tenant = Tenant.objects.first()

    if not tenant:
        print("ERROR: No tenant found. Please create a tenant first.")
        return None

    print(f"Using tenant: {tenant.name}")

    # Get or create "External Services" panel
    panel, created = NavigationPanel.objects.get_or_create(
        tenant=tenant,
        title="External Services",
        defaults={
            'description': 'External integrations and services (passthrough in progress)',
            'panel_type': 'external',
            'is_active': True,
            'sort_order': 100,
        }
    )

    if created:
        print("Created 'External Services' NavigationPanel")
    else:
        print("Found existing 'External Services' NavigationPanel")
        # Update description if needed
        if 'passthrough' not in panel.description.lower():
            panel.description = 'External integrations and services (passthrough in progress)'
            panel.save()

    # Notion - open in new window
    notion_item, notion_created = NavigationItem.objects.get_or_create(
        panel=panel,
        title='Notion',
        defaults={
            'url': 'https://www.notion.so',
            'item_type': 'link',
            'description': 'Notion workspace - passthrough integration in progress',
            'icon_style': 'emoji',
            'icon_value': '📝',
            'target': '_blank',  # Open in new window
            'is_active': True,
            'sort_order': 10,
            'requires_authentication': True,
        }
    )

    if notion_created:
        print("Created Notion navigation item")
    else:
        print("Notion navigation item already exists")
        # Update to ensure it opens in new window
        if notion_item.target != '_blank':
            notion_item.target = '_blank'
            notion_item.save()
            print("Updated Notion item to open in new window")

    # Airtable - open in new window
    airtable_item, airtable_created = NavigationItem.objects.get_or_create(
        panel=panel,
        title='Airtable',
        defaults={
            'url': 'https://airtable.com',
            'item_type': 'link',
            'description': 'Airtable workspace - passthrough integration in progress',
            'icon_style': 'emoji',
            'icon_value': '📊',
            'target': '_blank',  # Open in new window
            'is_active': True,
            'sort_order': 20,
            'requires_authentication': True,
        }
    )

    if airtable_created:
        print("Created Airtable navigation item")
    else:
        print("Airtable navigation item already exists")
        # Update to ensure it opens in new window
        if airtable_item.target != '_blank':
            airtable_item.target = '_blank'
            airtable_item.save()
            print("Updated Airtable item to open in new window")

    print("\n" + "="*60)
    print("External Services Setup Complete!")
    print("="*60)
    print(f"\nPanel: {panel.title}")
    print(f"  Description: {panel.description}")
    print(f"\nNavigation Items:")
    print(f"  1. {notion_item.title}")
    print(f"     URL: {notion_item.url}")
    print(f"     Target: {notion_item.target} (opens in new window)")
    print(f"     Icon: {'emoji' if notion_item.icon_value else 'None'}")
    print(f"\n  2. {airtable_item.title}")
    print(f"     URL: {airtable_item.url}")
    print(f"     Target: {airtable_item.target} (opens in new window)")
    print(f"     Icon: {'emoji' if airtable_item.icon_value else 'None'}")
    print("\nThese will appear in the sidebar under 'EXTERNAL SERVICES'")
    print("They open in new windows and can be explained as 'passthrough in progress'")
    print("\nNote: The panel description mentions 'passthrough in progress'")
    print("You can explain that these are being integrated with the passthrough system")

    return panel

if __name__ == '__main__':
    print("="*60)
    print("Setting up External Services (Notion & Airtable)")
    print("="*60)
    print()

    panel = setup_external_services()

    if panel:
        print("\nSetup successful!")
        print("\nNext steps:")
        print("1. Restart Django server if needed")
        print("2. Check sidebar - should see 'EXTERNAL SERVICES' section")
        print("3. Notion and Airtable links will open in new windows")
    else:
        print("\nSetup failed - check error messages above")

