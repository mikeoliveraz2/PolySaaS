#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# Setup Django
django.setup()

from dose.models import PassThroughEndpoint

# Find the endpoint with trigger_path='/admin/' (assuming it's Nextcloud)
endpoint = PassThroughEndpoint.objects.filter(trigger_path='/admin/').first()

if endpoint:
    print(f"Found endpoint: {endpoint.trigger_path} -> {endpoint.endpoint_url}")
    # Update to new path
    endpoint.trigger_path = '/pt/admin/nextcloud/'
    endpoint.bypass_middleware = True
    endpoint.save()
    print(f"Updated to: {endpoint.trigger_path}, bypass_middleware={endpoint.bypass_middleware}")
else:
    print("No endpoint found with trigger_path='/admin/'")

# List all endpoints for verification
print("\nAll PassThroughEndpoints:")
for ep in PassThroughEndpoint.objects.all():
    print(f"- {ep.trigger_path} -> {ep.endpoint_url} (enabled: {ep.is_enabled}, bypass: {ep.bypass_middleware})")