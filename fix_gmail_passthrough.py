#!/usr/bin/env python
"""
Fix Gmail passthrough endpoint configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*60)
print("Fixing Gmail Passthrough Endpoint")
print("="*60)
print()

# Find Gmail endpoint
gmail = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='gmail'
).first()

if not gmail:
    print("ERROR: Gmail endpoint not found!")
    exit(1)

print(f"Found Gmail endpoint ID: {gmail.id}")
print(f"  Current trigger_path: {gmail.trigger_path}")
print(f"  Current endpoint_url: {gmail.endpoint_url}")
print(f"  Current api_auth_type: {gmail.api_auth_type}")
print(f"  Current passthrough_type: {gmail.passthrough_type}")
print()

# Update configuration
print("Updating configuration...")
gmail.trigger_path = 'gmail'  # Simple name works with /pt/ routes
gmail.endpoint_url = 'https://gmail.googleapis.com/gmail/v1/users/me/'
gmail.is_enabled = True
gmail.show_in_menu = True
gmail.menu_title = 'Gmail'
gmail.menu_icon = '📧'
gmail.passthrough_type = 'api'  # Gmail is an API, not a scraper
gmail.bypass_middleware = False  # Let /pt/ routes handle it via GenericAPIPassthroughView
gmail.provider = 'google'
gmail.api_auth_type = 'oauth2'  # Use OAuth2, not bearer
gmail.integration_mode = 'web_api'  # Gmail has both web UI and API
gmail.description = 'Gmail API passthrough with OAuth2 authentication'
gmail.save()

print("Configuration updated!")
print()
print("="*60)
print("Gmail Endpoint Configuration:")
print("="*60)
print(f"  ID: {gmail.id}")
print(f"  Trigger Path: {gmail.trigger_path}")
print(f"  Endpoint URL: {gmail.endpoint_url}")
print(f"  Menu Title: {gmail.menu_title}")
print(f"  Show in Menu: {gmail.show_in_menu}")
print(f"  Enabled: {gmail.is_enabled}")
print(f"  Bypass Middleware: {gmail.bypass_middleware}")
print(f"  Passthrough Type: {gmail.passthrough_type}")
print(f"  Provider: {gmail.provider}")
print(f"  API Auth Type: {gmail.api_auth_type}")
print(f"  Integration Mode: {gmail.integration_mode}")
print()
print("Access URLs:")
print("  - http://localhost:8000/pt/admin/gmail/")
print("  - http://localhost:8000/pt/dose/gmail/")
print()
print("The endpoint should work with /pt/ routes via GenericAPIPassthroughView!")

