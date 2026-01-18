"""
Check v0 endpoint (ID: 4) status and configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import Tenant, PassThroughEndpoint
from django.test import RequestFactory
from dose.passthrough.handlers import get_handler_for_endpoint

print("="*80)
print("V0 ENDPOINT STATUS CHECK")
print("="*80)
print()

# Check v0 endpoint in olient schema
tenant = Tenant.objects.filter(schema_name='olient').first()
if not tenant:
    print("❌ olient tenant not found")
    exit(1)

print(f"Checking in tenant: {tenant.name} (schema: {tenant.schema_name})")
print()

try:
    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {tenant.schema_name},public;")

        # Find v0 endpoint
        v0_endpoints = PassThroughEndpoint.objects.filter(id=4)
        if not v0_endpoints.exists():
            print("❌ V0 endpoint (ID: 4) not found in olient schema")
            print("\nChecking all endpoints in olient:")
            all_eps = PassThroughEndpoint.objects.all()
            for ep in all_eps:
                print(f"  ID: {ep.id}, trigger_path: {ep.trigger_path}, endpoint_url: {ep.endpoint_url}")
            exit(1)

        v0 = v0_endpoints.first()
        print(f"✅ Found v0 endpoint (ID: {v0.id})")
        print()
        print("CONFIGURATION:")
        print(f"  ID: {v0.id}")
        print(f"  Trigger Path: {v0.trigger_path}")
        print(f"  Endpoint URL: {v0.endpoint_url}")
        print(f"  Menu Title: {v0.menu_title or '(empty)'}")
        print(f"  Passthrough Type: {v0.passthrough_type}")
        print(f"  Is Enabled: {v0.is_enabled}")
        print(f"  Show in Menu: {v0.show_in_menu}")
        print(f"  Handler Class: {v0.handler_class or '(not set)'}")
        print()

        # Check handler
        factory = RequestFactory()
        mock_request = factory.get('/dose/passthrough/4/')
        handler = get_handler_for_endpoint(v0, mock_request)

        print("HANDLER:")
        print(f"  Handler Class: {handler.__class__.__name__}")
        print(f"  Should Handle: {handler.should_handle()}")
        print()

        # Check URL routing
        from django.urls import reverse
        try:
            url = reverse('dose:passthrough_scraper', args=[v0.id])
            print(f"  URL: {url}")
        except Exception as e:
            print(f"  ❌ URL Error: {e}")

        print()
        print("BASE URL:")
        base_url = handler.get_base_url(v0.endpoint_url)
        print(f"  Base URL: {base_url}")

        print()
        print("STATUS:")
        if v0.is_enabled and v0.show_in_menu:
            print("  ✅ Endpoint is enabled and will appear in sidebar")
        else:
            print("  ⚠️  Endpoint may not appear in sidebar:")
            if not v0.is_enabled:
                print("     - is_enabled = False")
            if not v0.show_in_menu:
                print("     - show_in_menu = False")

        if handler.__class__.__name__ == 'V0PassthroughHandler':
            print("  ✅ Using V0PassthroughHandler (correct)")
        else:
            print(f"  ⚠️  Using {handler.__class__.__name__} (expected V0PassthroughHandler)")

        print()
        print("RECOMMENDATIONS:")
        if not v0.menu_title:
            print("  ⚠️  menu_title is empty - sidebar will show 'v0' as title")
        if v0.handler_class != 'V0PassthroughHandler':
            print(f"  ⚠️  handler_class is '{v0.handler_class}' but should be 'V0PassthroughHandler'")
            print("     (This will be auto-updated on next request)")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)

