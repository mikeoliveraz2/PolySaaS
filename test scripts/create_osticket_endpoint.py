#!/usr/bin/env python3
"""Create OSTicket PassThroughEndpoint"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from dose.models import PassThroughEndpoint

# Delete any existing OSTicket endpoints
existing = PassThroughEndpoint.objects.filter(trigger_path__icontains='osticket')
if existing.exists():
    print(f"⚠️  Deleting {existing.count()} existing OSTicket endpoints...")
    existing.delete()

# Create OSTicket endpoint
endpoint = PassThroughEndpoint.objects.create(
    trigger_path='osticket',  # Will match /pt/admin/osticket/ or /pt/dose/osticket/
    endpoint_url='https://oliverenterprises.app.saasify.cloud/scp/',
    is_enabled=True,
    provider='custom',
    description='OSTicket Support System',
    show_in_menu=True,
    menu_title='OSTicket Support',
    menu_icon='fas fa-ticket-alt',
    passthrough_type='scraper',  # HTML-based, not JSON API
    integration_mode='web_only',
    api_auth_type='bearer'
)

print(f"✅ Created OSTicket endpoint:")
print(f"   ID: {endpoint.id}")
print(f"   trigger_path: {endpoint.trigger_path}")
print(f"   endpoint_url: {endpoint.endpoint_url}")
print(f"   is_enabled: {endpoint.is_enabled}")

# List all endpoints
print("\n📋 All enabled endpoints:")
for ep in PassThroughEndpoint.objects.filter(is_enabled=True):
    print(f"   trigger_path: {ep.trigger_path} → {ep.endpoint_url}")
