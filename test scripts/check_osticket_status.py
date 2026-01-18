#!/usr/bin/env python
"""
Check current OS ticket configuration status
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*60)
print("OS Ticket Configuration Status")
print("="*60)
print()

# Find all OS ticket endpoints
osticket_endpoints = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='osticket'
) | PassThroughEndpoint.objects.filter(
    endpoint_url__icontains='oliverenterprises'
)

if osticket_endpoints.exists():
    print(f"Found {osticket_endpoints.count()} OS ticket endpoint(s):\n")
    for ep in osticket_endpoints:
        print(f"ID: {ep.id}")
        print(f"  Trigger Path: {ep.trigger_path}")
        print(f"  Endpoint URL: {ep.endpoint_url}")
        print(f"  Enabled: {ep.is_enabled}")
        print(f"  Show in Menu: {ep.show_in_menu}")
        print(f"  Menu Title: {ep.menu_title or 'Not set'}")
        print(f"  Passthrough Type: {ep.passthrough_type}")
        print(f"  Bypass Middleware: {ep.bypass_middleware}")
        print()
else:
    print("No OS ticket endpoints found in database!")
    print("You may need to run: python setup_osticket_endpoint.py")

print("="*60)
print("Access URLs:")
print("  - http://localhost:8000/admin/osticket/")
print("  - http://localhost:8000/pt/admin/osticket/")
print("="*60)

