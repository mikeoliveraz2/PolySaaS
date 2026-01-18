#!/usr/bin/env python
"""
Update Monitor Logger endpoint URL to use monitorlogger.com
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*60)
print("Updating Monitor Logger Endpoint URL")
print("="*60)
print()

# Find Monitor Logger endpoint
monitor = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='monitor'
).first()

if not monitor:
    print("ERROR: Monitor Logger endpoint not found!")
    exit(1)

print(f"Found Monitor Logger endpoint ID: {monitor.id}")
print(f"  Current endpoint_url: {monitor.endpoint_url}")
print()

# Update to use monitorlogger.com
print("Updating endpoint URL to monitorlogger.com:5000...")
monitor.endpoint_url = 'http://monitorlogger.com:5000'
monitor.save()

print("Configuration updated!")
print()
print("="*60)
print("Monitor Logger Endpoint Configuration:")
print("="*60)
print(f"  ID: {monitor.id}")
print(f"  Trigger Path: {monitor.trigger_path}")
print(f"  Endpoint URL: {monitor.endpoint_url}")
print(f"  Bypass Middleware: {monitor.bypass_middleware}")
print(f"  Enabled: {monitor.is_enabled}")
print()
print("Access URLs:")
print("  - http://localhost:8000/pt/admin/monitor-logger/")
print()
print("The endpoint will proxy to: http://monitorlogger.com:5000")
print("(Make sure your hosts file maps monitorlogger.com to 127.0.0.1)")

