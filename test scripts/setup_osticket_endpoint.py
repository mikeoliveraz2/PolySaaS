#!/usr/bin/env python
"""
Setup script to configure OSTicket PassthroughEndpoint.
The middleware at /admin/osticket/ forwards requests directly to OSTicket.
No iframe - just direct middleware passthrough.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

# OSTicket configuration
TRIGGER_PATH = '/admin/osticket/'
ENDPOINT_URL = 'https://oliverenterprises.app.saasify.cloud/scp/dashboard.php'

print(f"[OSTicket Setup] Configuring PassthroughEndpoint...")
print(f"  Trigger Path: {TRIGGER_PATH}")
print(f"  Endpoint URL: {ENDPOINT_URL}")

# Check if endpoint already exists
existing = PassThroughEndpoint.objects.filter(trigger_path=TRIGGER_PATH).first()

if existing:
    print(f"[OSTicket Setup] Found existing endpoint: {existing.id}")
    print(f"  Current URL: {existing.endpoint_url}")
    print(f"  Enabled: {existing.is_enabled}")

    # Update endpoint URL if different
    if existing.endpoint_url != ENDPOINT_URL:
        print(f"[OSTicket Setup] Updating endpoint URL...")
        existing.endpoint_url = ENDPOINT_URL
        existing.save()
        print(f"[OSTicket Setup] [OK] Endpoint URL updated")

    # Enable if disabled
    if not existing.is_enabled:
        print(f"[OSTicket Setup] Enabling endpoint...")
        existing.is_enabled = True
        existing.save()
        print(f"[OSTicket Setup] [OK] Endpoint enabled")
else:
    print(f"[OSTicket Setup] Creating new endpoint...")
    endpoint = PassThroughEndpoint.objects.create(
        trigger_path=TRIGGER_PATH,
        endpoint_url=ENDPOINT_URL,
        is_enabled=True,
        description='OSTicket passthrough - middleware forwards /admin/osticket/ to external server'
    )
    print(f"[OSTicket Setup] [OK] Endpoint created: {endpoint.id}")

# Disable old endpoints with other paths (if any)
old_endpoints = PassThroughEndpoint.objects.exclude(trigger_path=TRIGGER_PATH).filter(endpoint_url__contains='osticket', is_enabled=True)
if old_endpoints.exists():
    print(f"[OSTicket Setup] Disabling old OSTicket endpoints with different paths...")
    for ep in old_endpoints:
        print(f"  Disabling: {ep.id} (trigger_path={ep.trigger_path})")
        ep.is_enabled = False
        ep.save()
    print(f"[OSTicket Setup] [OK] Old endpoints disabled")

print(f"[OSTicket Setup] [OK] Configuration complete!")
print(f"[OSTicket Setup] Access OSTicket at: http://localhost:8000/admin/osticket/")
print(f"[OSTicket Setup] Middleware will intercept and forward to external server")
