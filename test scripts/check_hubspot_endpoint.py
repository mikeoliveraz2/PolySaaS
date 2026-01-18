#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

# Check all PassThroughEndpoint records
endpoints = PassThroughEndpoint.objects.all()
print(f"Total endpoints: {endpoints.count()}\n")

for ep in endpoints:
    print(f"ID: {ep.id}")
    print(f"  URL: {ep.endpoint_url}")
    print(f"  Menu Title: {ep.menu_title}")
    print(f"  Trigger Path: {ep.trigger_path}")
    print(f"  Is Enabled: {ep.is_enabled}")
    print(f"  Show in Menu: {ep.show_in_menu}")
    print(f"  Menu Icon: {ep.menu_icon}")
    print()

# Check specifically for Hubspot
hubspot = PassThroughEndpoint.objects.filter(description__icontains='hubspot').first()
if hubspot:
    print("\n✅ HubSpot found!")
    print(f"  is_enabled: {hubspot.is_enabled}")
    print(f"  show_in_menu: {hubspot.show_in_menu}")
    print(f"  trigger_path: {hubspot.trigger_path}")
else:
    print("\n❌ HubSpot NOT found")
