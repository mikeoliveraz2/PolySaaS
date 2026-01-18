#!/usr/bin/env python
"""
Check Gmail passthrough endpoint configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*60)
print("Gmail Passthrough Endpoint Check")
print("="*60)
print()

# Find all Gmail endpoints
gmail_endpoints = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='gmail'
) | PassThroughEndpoint.objects.filter(
    endpoint_url__icontains='gmail'
)

if gmail_endpoints.exists():
    print(f"Found {gmail_endpoints.count()} Gmail endpoint(s):\n")
    for ep in gmail_endpoints:
        print(f"ID: {ep.id}")
        print(f"  Trigger Path: {ep.trigger_path}")
        print(f"  Endpoint URL: {ep.endpoint_url}")
        print(f"  Menu Title: {ep.menu_title or 'Not set'}")
        print(f"  Show in Menu: {ep.show_in_menu}")
        print(f"  Enabled: {ep.is_enabled}")
        print(f"  Bypass Middleware: {ep.bypass_middleware}")
        print(f"  Passthrough Type: {ep.passthrough_type}")
        print(f"  Provider: {ep.provider}")
        print(f"  API Auth Type: {ep.api_auth_type}")
        print(f"  Integration Mode: {ep.integration_mode}")
        print()
else:
    print("No Gmail endpoints found!")
    print("\nCreating default Gmail endpoint...")
    ep = PassThroughEndpoint.objects.create(
        trigger_path='gmail',
        endpoint_url='https://gmail.googleapis.com/gmail/v1',
        is_enabled=True,
        show_in_menu=True,
        menu_title='Gmail',
        menu_icon='📧',
        passthrough_type='api',
        bypass_middleware=True,
        provider='google',
        api_auth_type='oauth2',
        integration_mode='web_api',
        description='Gmail API passthrough with OAuth2 authentication'
    )
    print(f"Created endpoint ID: {ep.id}")
    print(f"  Trigger Path: {ep.trigger_path}")
    print(f"  Endpoint URL: {ep.endpoint_url}")

print("="*60)
print("URL Routing Check:")
print("="*60)

# Check if /pt/admin/gmail/ and /pt/dose/gmail/ are handled
print("Expected URLs:")
print("  - /pt/admin/gmail/ (should use GenericAPIPassthroughView)")
print("  - /pt/dose/gmail/ (should use GenericAPIPassthroughView)")
print("  - /admin/gmail/ (legacy - may use dedicated view)")
print("  - /dose/gmail/ (legacy - may use dedicated view)")
print()

# Check URL patterns
from django.urls import get_resolver
resolver = get_resolver()
patterns = []
for pattern in resolver.url_patterns:
    if hasattr(pattern, 'pattern'):
        pattern_str = str(pattern.pattern)
        if 'gmail' in pattern_str.lower() or 'pt' in pattern_str.lower():
            patterns.append(pattern_str)

if patterns:
    print("Found URL patterns:")
    for p in patterns:
        print(f"  - {p}")
else:
    print("No Gmail URL patterns found in URL resolver")

print()
print("="*60)
print("Recommendations:")
print("="*60)

# Check the primary endpoint
primary = PassThroughEndpoint.objects.filter(trigger_path__icontains='gmail').first()
if primary:
    if not primary.is_enabled:
        print("WARNING: Gmail endpoint is DISABLED - enable it!")
    if primary.passthrough_type != 'api':
        print(f"WARNING: Passthrough type is '{primary.passthrough_type}', should be 'api' for Gmail")
    if primary.provider != 'google':
        print(f"WARNING: Provider is '{primary.provider}', should be 'google' for Gmail")
    if primary.api_auth_type != 'oauth2':
        print(f"WARNING: API auth type is '{primary.api_auth_type}', should be 'oauth2' for Gmail")
    if primary.bypass_middleware:
        print("INFO: Bypass middleware is True - using dedicated view")
    else:
        print("INFO: Bypass middleware is False - using passthrough middleware")
    print(f"OK: Endpoint configured: {primary.trigger_path} -> {primary.endpoint_url}")
else:
    print("ERROR: No Gmail endpoint found")
    print("   Run this script again to create one")
