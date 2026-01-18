#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import RequestFactory
from dose.middleware.jazzmin_tenant_theme import JazzminTenantThemeMiddleware
from dose.models.pass_through_endpoint import PassThroughEndpoint
from django_tenants.utils import get_tenant_model

def test_dynamic_menu_integration():
    print("=== Testing Dynamic Menu Integration ===")

    # Get our test data
    endpoints = PassThroughEndpoint.objects.all()
    print(f"Found {endpoints.count()} PassThroughEndpoint records:")

    for endpoint in endpoints:
        print(f"  - {endpoint.menu_title or 'No Title'}: {endpoint.trigger_path} (show_in_menu: {endpoint.show_in_menu})")

    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/admin/')

    # Get a tenant
    Tenant = get_tenant_model()
    tenant = Tenant.objects.first()
    if tenant:
        request.tenant = tenant
        print(f"\nTesting with tenant: {tenant.name}")

        # Create middleware and process request
        middleware = JazzminTenantThemeMiddleware(get_response=lambda req: None)
        middleware.process_request(request)

        # Check if jazzmin_settings was created
        if hasattr(request, 'jazzmin_settings'):
            topmenu_links = request.jazzmin_settings.get('topmenu_links', [])
            print(f"\nGenerated topmenu_links ({len(topmenu_links)} items):")

            for i, link in enumerate(topmenu_links, 1):
                name = link.get('name', 'Unknown')
                url = link.get('url', 'No URL')
                print(f"  {i}. {name} -> {url}")

            # Check if Gmail is included
            gmail_links = [link for link in topmenu_links if 'Gmail' in link.get('name', '')]
            if gmail_links:
                print(f"\n✅ SUCCESS: Gmail found in menu! {gmail_links[0]}")
            else:
                print(f"\n❌ ISSUE: Gmail not found in generated menu")

            # Check if OSTicket is still there
            osticket_links = [link for link in topmenu_links if 'OSTicket' in link.get('name', '')]
            if osticket_links:
                print(f"✅ OSTicket still present: {osticket_links[0]}")
            else:
                print(f"⚠️  OSTicket not found in menu")

        else:
            print("❌ ERROR: No jazzmin_settings found on request")
    else:
        print("❌ ERROR: No tenant found")

if __name__ == "__main__":
    test_dynamic_menu_integration()