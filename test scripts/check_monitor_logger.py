#!/usr/bin/env python
"""
Check Monitor Logger endpoint configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*60)
print("Monitor Logger Endpoint Check")
print("="*60)
print()

# Find Monitor Logger endpoint
monitor = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='monitor'
).first()

if monitor:
    print(f"Found Monitor Logger endpoint:")
    print(f"  ID: {monitor.id}")
    print(f"  Trigger Path: {monitor.trigger_path}")
    print(f"  Endpoint URL: {monitor.endpoint_url}")
    print(f"  Menu Title: {monitor.menu_title}")
    print(f"  Show in Menu: {monitor.show_in_menu}")
    print(f"  Enabled: {monitor.is_enabled}")
    print(f"  Bypass Middleware: {monitor.bypass_middleware}")
    print(f"  Passthrough Type: {monitor.passthrough_type}")
    print()

    # Check if Flask service is running
    import requests
    try:
        response = requests.get("http://localhost:5000/", timeout=2)
        if response.status_code == 200:
            print("Flask Monitor Logger Service: RUNNING")
        else:
            print(f"Flask Monitor Logger Service: Responding with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Flask Monitor Logger Service: NOT RUNNING")
        print("  Start it with: cd pass_through_service && python app.py")
    except Exception as e:
        print(f"Flask Monitor Logger Service: Error checking - {e}")
else:
    print("ERROR: Monitor Logger endpoint not found!")
    print("Run: python setup_demo_endpoint.py")

print()
print("="*60)
print("Issues to check:")
print("="*60)

if monitor:
    if monitor.bypass_middleware:
        print("WARNING: bypass_middleware=True - this might prevent /pt/ routes from working")
        print("  Should be False for /pt/ routes to work")
    if not monitor.is_enabled:
        print("ERROR: Endpoint is DISABLED")
    if monitor.passthrough_type != 'scraper':
        print(f"WARNING: passthrough_type is '{monitor.passthrough_type}', should be 'scraper'")

