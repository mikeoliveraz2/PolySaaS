#!/usr/bin/env python
"""
Test Gmail /pt/ route configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from dose.generic_passthrough_views_deprecated import GenericAPIPassthroughView

print("="*60)
print("Gmail /pt/ Route Test")
print("="*60)
print()

# Test endpoint lookup
view = GenericAPIPassthroughView()
test_paths = [
    '/pt/admin/gmail/',
    '/pt/admin/gmail/messages',
    '/pt/admin/gmail/messages/123',
]

for test_path in test_paths:
    print(f"Testing: {test_path}")
    endpoint = view.get_endpoint_config(test_path)
    if endpoint:
        print(f"  [OK] Found endpoint:")
        print(f"    Trigger: {endpoint.trigger_path}")
        print(f"    Type: {endpoint.passthrough_type}")
        print(f"    URL: {endpoint.endpoint_url}")
        print(f"    Enabled: {endpoint.is_enabled}")

        # Test path extraction
        from dose.generic_passthrough_views_deprecated import extract_pt_path
        ext_path = extract_pt_path(test_path, endpoint)
        print(f"    Extracted path: '{ext_path}'")

        # Show what target URL would be
        if ext_path:
            target_url = f"{endpoint.endpoint_url.rstrip('/')}/{ext_path}"
        else:
            target_url = endpoint.endpoint_url.rstrip('/')
        print(f"    Target URL: {target_url}")
    else:
        print(f"  [ERROR] No endpoint found!")
    print()

print("="*60)
print("Gmail Endpoint Direct Check")
print("="*60)
gmail = PassThroughEndpoint.objects.filter(trigger_path__icontains='gmail').first()
if gmail:
    print(f"  Trigger: {gmail.trigger_path}")
    print(f"  Type: {gmail.passthrough_type}")
    print(f"  URL: {gmail.endpoint_url}")
    print(f"  Enabled: {gmail.is_enabled}")
    print(f"  Bypass Middleware: {gmail.bypass_middleware}")
else:
    print("  [ERROR] Gmail endpoint not found in database!")

print()
print("="*60)
print("Summary")
print("="*60)
print("Gmail should be accessible at: /pt/admin/gmail/")
print("API calls should work at: /pt/admin/gmail/messages, etc.")
print("All routes use the /pt/ prefix for consistency.")

