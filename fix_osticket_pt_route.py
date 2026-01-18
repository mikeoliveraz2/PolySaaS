#!/usr/bin/env python
"""
Fix OSTicket endpoint for /pt/ routes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*60)
print("Fixing OSTicket for /pt/ routes")
print("="*60)
print()

# Find OSTicket endpoint
osticket = PassThroughEndpoint.objects.filter(trigger_path__icontains='osticket').first()

if not osticket:
    print("ERROR: OSTicket endpoint not found!")
    exit(1)

print(f"Current OSTicket configuration:")
print(f"  Trigger Path: {osticket.trigger_path}")
print(f"  Endpoint URL: {osticket.endpoint_url}")
print(f"  Passthrough Type: {osticket.passthrough_type}")
print(f"  Bypass Middleware: {osticket.bypass_middleware}")
print()

# Update for /pt/ routes
print("Updating for /pt/ routes...")
osticket.trigger_path = 'osticket'  # Simple name for /pt/admin/osticket/
osticket.endpoint_url = 'https://oliverenterprises.app.saasify.cloud/scp/'  # Correct base URL
osticket.passthrough_type = 'scraper'  # HTML scraping
osticket.bypass_middleware = False  # Let /pt/ routes handle it via GenericScraperPassthroughView
osticket.is_enabled = True
osticket.provider = 'custom'
osticket.api_auth_type = 'oauth2'  # Use OAuth2 if configured
osticket.save()

print("Configuration updated!")
print()
print("="*60)
print("OSTicket Endpoint Configuration:")
print("="*60)
print(f"  Trigger Path: {osticket.trigger_path}")
print(f"  Endpoint URL: {osticket.endpoint_url}")
print(f"  Passthrough Type: {osticket.passthrough_type}")
print(f"  Bypass Middleware: {osticket.bypass_middleware}")
print(f"  Provider: {osticket.provider}")
print(f"  API Auth Type: {osticket.api_auth_type}")
print()
print("Access URLs:")
print("  - http://localhost:8000/pt/admin/osticket/ (via GenericScraperPassthroughView)")
print("  - http://localhost:8000/admin/osticket/ (via dedicated osticket_admin_view)")
print()
print("Both should work now!")

