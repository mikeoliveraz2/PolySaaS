#!/usr/bin/env python
"""
Create v0.dev PassThroughEndpoint for demo
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*60)
print("Creating v0.dev PassThroughEndpoint")
print("="*60)
print()

# Check if v0 endpoint already exists
v0 = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='v0'
).first()

if v0:
    print(f"⚠️  v0 endpoint already exists (ID: {v0.id})")
    print(f"   Trigger path: {v0.trigger_path}")
    print(f"   Type: {v0.passthrough_type}")
    print(f"   Enabled: {v0.is_enabled}")
    print(f"   Show in menu: {v0.show_in_menu}")
    print()
    print("Updating configuration...")
    v0.trigger_path = 'v0'
    v0.endpoint_url = 'https://v0.dev'
    v0.passthrough_type = 'scraper'  # Must be scraper to use GenericScraperPassthroughView which uses handlers
    v0.is_enabled = True
    v0.show_in_menu = True
    v0.menu_title = 'v0'
    v0.menu_icon = '🔗'
    v0.description = 'v0.dev - AI-powered UI builder'
    v0.save()
    print("✅ Updated v0 endpoint")
else:
    print("Creating new v0 endpoint...")
    v0 = PassThroughEndpoint.objects.create(
        trigger_path='v0',
        endpoint_url='https://v0.dev',
        passthrough_type='scraper',  # Must be scraper to use GenericScraperPassthroughView which uses handlers
        is_enabled=True,
        show_in_menu=True,
        menu_title='v0',
        menu_icon='🔗',
        description='v0.dev - AI-powered UI builder',
        provider='custom'
    )
    print(f"✅ Created v0 endpoint (ID: {v0.id})")

print()
print("="*60)
print("v0 Endpoint Configuration:")
print("="*60)
print(f"  ID: {v0.id}")
print(f"  Trigger Path: {v0.trigger_path}")
print(f"  Endpoint URL: {v0.endpoint_url}")
print(f"  Passthrough Type: {v0.passthrough_type}")
print(f"  Menu Title: {v0.menu_title}")
print(f"  Show in Menu: {v0.show_in_menu}")
print(f"  Enabled: {v0.is_enabled}")
print()
print("✅ v0 endpoint is now configured!")
print("   The V0PassthroughHandler will be used automatically")
print("   Access via: /pt/admin/v0/ or /pt/dose/v0/")

