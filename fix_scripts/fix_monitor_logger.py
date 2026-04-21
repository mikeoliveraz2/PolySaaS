#!/usr/bin/env python
"""
Fix Monitor Logger endpoint configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*60)
print("Fixing Monitor Logger Endpoint")
print("="*60)
print()

# Find Monitor Logger endpoint
monitor = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='monitor'
).first()

if not monitor:
    print("ERROR: Monitor Logger endpoint not found!")
    print("Run: python setup_demo_endpoint.py")
    exit(1)

print(f"Found Monitor Logger endpoint ID: {monitor.id}")
print(f"  Current trigger_path: {monitor.trigger_path}")
print(f"  Current endpoint_url: {monitor.endpoint_url}")
print(f"  Current bypass_middleware: {monitor.bypass_middleware}")
print()

# Update configuration
print("Updating configuration...")
monitor.trigger_path = 'monitor-logger'  # Keep hyphenated name
monitor.endpoint_url = 'http://localhost:5000'  # Fix URL
monitor.is_enabled = True
monitor.show_in_menu = True
monitor.menu_title = 'Monitor Logger'
monitor.menu_icon = '📊'
monitor.passthrough_type = 'scraper'  # HTML content
monitor.bypass_middleware = False  # Let /pt/ routes handle it via GenericScraperPassthroughView
monitor.provider = 'custom'
monitor.description = 'Real-time monitoring and logging service - intercepts and logs events'
monitor.save()

print("Configuration updated!")
print()
print("="*60)
print("Monitor Logger Endpoint Configuration:")
print("="*60)
print(f"  ID: {monitor.id}")
print(f"  Trigger Path: {monitor.trigger_path}")
print(f"  Endpoint URL: {monitor.endpoint_url}")
print(f"  Menu Title: {monitor.menu_title}")
print(f"  Show in Menu: {monitor.show_in_menu}")
print(f"  Enabled: {monitor.is_enabled}")
print(f"  Bypass Middleware: {monitor.bypass_middleware}")
print(f"  Passthrough Type: {monitor.passthrough_type}")
print()
print("Access URLs:")
print("  - http://localhost:8000/pt/admin/monitor-logger/")
print("  - http://localhost:8000/pt/dose/monitor-logger/")
print()
print("The endpoint should work with /pt/ routes via GenericScraperPassthroughView!")

