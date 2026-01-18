#!/usr/bin/env python
"""
Fix OSTicket PassThroughEndpoint configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*60)
print("Fixing OSTicket PassThroughEndpoint")
print("="*60)
print()

# Find OSTicket endpoint
osticket = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='osticket'
).first()

if not osticket:
    print("ERROR: No OSTicket endpoint found!")
    print("Creating new endpoint...")
    osticket = PassThroughEndpoint.objects.create(
        trigger_path='osticket',  # Simple name - will match /admin/osticket/ and /pt/admin/osticket/
        endpoint_url='https://oliverenterprises.app.saasify.cloud/scp/dashboard.php',
        is_enabled=True,
        show_in_menu=True,
        menu_title='OSTicket',
        menu_icon='🎫',
        passthrough_type='scraper',
        bypass_middleware=True,
        integration_mode='web_only',
        description='OSTicket passthrough - middleware forwards to external server'
    )
    print(f"Created endpoint ID: {osticket.id}")
else:
    print(f"Found OSTicket endpoint ID: {osticket.id}")
    print(f"  Current trigger_path: {osticket.trigger_path}")
    print(f"  Current endpoint_url: {osticket.endpoint_url}")
    print()

# Ensure it's properly configured
print("Updating configuration...")
osticket.trigger_path = 'osticket'  # Simple name works with middleware
osticket.endpoint_url = 'https://oliverenterprises.app.saasify.cloud/scp/login.php'  # Use login page, not dashboard
osticket.is_enabled = True
osticket.show_in_menu = True
osticket.menu_title = 'OSTicket'
osticket.menu_icon = '🎫'
osticket.passthrough_type = 'scraper'
osticket.bypass_middleware = True  # Use dedicated view if available
osticket.integration_mode = 'web_only'
osticket.description = 'OSTicket passthrough - middleware forwards to external server'
osticket.save()

print("Configuration updated!")
print()
print("="*60)
print("OSTicket Endpoint Configuration:")
print("="*60)
print(f"  ID: {osticket.id}")
print(f"  Trigger Path: {osticket.trigger_path}")
print(f"  Endpoint URL: {osticket.endpoint_url}")
print(f"  Menu Title: {osticket.menu_title}")
print(f"  Show in Menu: {osticket.show_in_menu}")
print(f"  Enabled: {osticket.is_enabled}")
print(f"  Bypass Middleware: {osticket.bypass_middleware}")
print(f"  Passthrough Type: {osticket.passthrough_type}")
print()
print("Access URLs:")
print("  - http://localhost:8000/admin/osticket/")
print("  - http://localhost:8000/pt/admin/osticket/")
print()
print("The endpoint should work with both paths!")

