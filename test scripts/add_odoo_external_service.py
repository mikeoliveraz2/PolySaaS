#!/usr/bin/env python
"""
Add Odoo as an external service navigation item.
Opens in new window - passthrough integration planned for future.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import NavigationPanel, NavigationItem, Tenant
from django.contrib.auth.models import User

def add_odoo_external_service(odoo_url=None):
    """Add Odoo to External Services panel"""

    # Get Oliver Enterprises tenant (or first tenant)
    tenant = Tenant.objects.filter(name__icontains='oliver').first()
    if not tenant:
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

    # Default Odoo URL if not provided
    if not odoo_url:
        odoo_url = 'https://www.odoo.com'  # Placeholder - update with actual URL

    # Odoo - open in new window
    odoo_item, odoo_created = NavigationItem.objects.get_or_create(
        panel=panel,
        title='Odoo',
        defaults={
            'url': odoo_url,
            'item_type': 'link',
            'description': 'Odoo ERP - passthrough integration planned for future',
            'icon_style': 'emoji',
            'icon_value': '📦',  # Package/box icon for ERP
            'target': '_blank',  # Open in new window
            'is_active': True,
            'sort_order': 30,  # After Notion (10) and Airtable (20)
            'requires_authentication': True,
        }
    )

    if odoo_created:
        print(f"Created Odoo navigation item")
        print(f"  URL: {odoo_url}")
    else:
        print("Odoo navigation item already exists")
        # Update URL if it changed
        if odoo_item.url != odoo_url:
            odoo_item.url = odoo_url
            odoo_item.save()
            print(f"Updated Odoo URL to: {odoo_url}")
        # Update to ensure it opens in new window
        if odoo_item.target != '_blank':
            odoo_item.target = '_blank'
            odoo_item.save()
            print("Updated Odoo item to open in new window")

    print("\n" + "="*60)
    print("Odoo External Service Setup Complete!")
    print("="*60)
    print(f"\nPanel: {panel.title} (Tenant: {panel.tenant.name})")
    print(f"\nNavigation Item:")
    print(f"  Title: {odoo_item.title}")
    print(f"  URL: {odoo_item.url}")
    print(f"  Target: {odoo_item.target} (opens in new window)")
    print(f"  Icon: {odoo_item.icon_value}")
    print(f"  Description: {odoo_item.description}")
    print("\nOdoo will appear in the sidebar under 'EXTERNAL SERVICES'")
    print("It will open in a new window and can be explained as 'passthrough planned'")

    return odoo_item

if __name__ == '__main__':
    import sys

    print("="*60)
    print("Adding Odoo to External Services")
    print("="*60)
    print()

    # Get Odoo URL from command line if provided
    odoo_url = None
    if len(sys.argv) > 1:
        odoo_url = sys.argv[1]
        print(f"Using provided Odoo URL: {odoo_url}")
    else:
        print("No URL provided - using placeholder: https://www.odoo.com")
        print("To update, run: python add_odoo_external_service.py <your-odoo-url>")
        print()

    item = add_odoo_external_service(odoo_url)

    if item:
        print("\nSetup successful!")
        print("\nNext steps:")
        print("1. If you used a placeholder URL, update it in the admin interface")
        print("   or run: python add_odoo_external_service.py <your-actual-odoo-url>")
        print("2. Restart Django server if needed")
        print("3. Check sidebar - should see 'Odoo' under 'EXTERNAL SERVICES'")
        print("4. Odoo link will open in new window")
    else:
        print("\nSetup failed - check error messages above")

