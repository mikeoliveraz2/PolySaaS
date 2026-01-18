#!/usr/bin/env python
"""
Check Airtable NavigationItem
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import NavigationItem, NavigationPanel
from django.contrib.auth.models import User

print("="*60)
print("Airtable NavigationItem Check")
print("="*60)
print()

# Find Airtable item
item = NavigationItem.objects.filter(title='Airtable').first()

if item:
    print(f"Airtable Item:")
    print(f"  ID: {item.id}")
    print(f"  Title: {item.title}")
    print(f"  Panel: {item.panel.title}")
    print(f"  Panel Tenant: {item.panel.tenant.name if item.panel.tenant else 'None'}")
    print(f"  Panel Active: {item.panel.is_active}")
    print(f"  Item Active: {item.is_active}")
    print(f"  Requires Auth: {item.requires_authentication}")
    print(f"  Requires Perms: '{item.requires_permissions}'")
    print(f"  URL: {item.url}")
    print(f"  Target: {item.target}")
    print(f"  Item Type: {item.item_type}")
    print()

    # Check permissions for a test user
    user = User.objects.filter(username__icontains='olient').first()
    if user:
        has_perm = item.has_permission(user)
        print(f"Permission check for {user.username}:")
        print(f"  has_permission: {has_perm}")
        print(f"  user.is_authenticated: {user.is_authenticated}")
        print(f"  user.is_staff: {user.is_staff}")
else:
    print("ERROR: Airtable NavigationItem not found!")

print()
print("="*60)
print("All External Services Items:")
print("="*60)

# Get all items in External Services panels
panels = NavigationPanel.objects.filter(title__icontains='External Services', is_active=True)
for panel in panels:
    print(f"\nPanel: {panel.title} (Tenant: {panel.tenant.name})")
    items = NavigationItem.objects.filter(panel=panel, is_active=True)
    for item in items:
        print(f"  - {item.title} (Active: {item.is_active}, URL: {item.url})")

