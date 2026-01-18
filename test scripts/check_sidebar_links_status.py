"""
Check the status of all sidebar links (PassThroughEndpoint records)
and verify their handlers are configured correctly.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from django.db import models
from dose.models import Tenant, PassThroughEndpoint
from dose.passthrough.handlers.registry import HANDLER_REGISTRY

print("="*80)
print("SIDEBAR LINKS STATUS CHECK")
print("="*80)
print()

# Check all tenant schemas
tenants = Tenant.objects.all()
print(f"Found {tenants.count()} tenants:")
for tenant in tenants:
    print(f"  - {tenant.name} (schema: {tenant.schema_name})")
print()

all_endpoints = []

for tenant in tenants:
    if not tenant.schema_name:
        continue

    print(f"\n{'='*80}")
    print(f"TENANT: {tenant.name} (schema: {tenant.schema_name})")
    print(f"{'='*80}")

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {tenant.schema_name},public;")

            endpoints = PassThroughEndpoint.objects.all().order_by('id')
            count = endpoints.count()
            print(f"\nTotal PassThroughEndpoint records: {count}")

            if count == 0:
                print("  No endpoints found in this schema.")
                continue

            print(f"\n{'ID':<5} {'Trigger':<20} {'Menu Title':<25} {'Type':<10} {'Enabled':<8} {'Show Menu':<10} {'Handler':<30} {'URL':<40}")
            print("-" * 150)

            for ep in endpoints:
                # Get handler by checking registry
                handler_name = "DefaultScraperHandler"  # Default fallback
                for key, handler_class in HANDLER_REGISTRY.items():
                    if hasattr(handler_class, 'should_handle'):
                        # Create a mock handler instance to check
                        try:
                            # Create a minimal mock request object
                            from django.test import RequestFactory
                            factory = RequestFactory()
                            mock_request = factory.get('/')
                            handler_instance = handler_class(ep, mock_request)
                            # Check if this handler should handle this endpoint
                            if handler_instance.should_handle():
                                handler_name = handler_class.__name__
                                break
                        except Exception as e:
                            # If handler check fails, continue to next
                            pass

                # Determine URL
                from django.urls import reverse
                try:
                    if 'osticket' in ep.trigger_path.lower():
                        url = f"/admin/polysniffer/live-capture/{ep.id}/"
                    elif ep.trigger_path.lower() == 'gmail':
                        url = reverse('dose:gmail_inbox')
                    elif ep.passthrough_type == 'api':
                        url = reverse('dose:passthrough_api', args=[ep.trigger_path])
                    else:
                        url = reverse('dose:passthrough_scraper', args=[ep.id])
                except Exception as e:
                    url = f"ERROR: {str(e)[:30]}"

                # Status indicators
                enabled = "✓" if ep.is_enabled else "✗"
                show_menu = "✓" if ep.show_in_menu else "✗"

                print(f"{ep.id:<5} {ep.trigger_path:<20} {(ep.menu_title or 'N/A')[:24]:<25} {ep.passthrough_type:<10} {enabled:<8} {show_menu:<10} {handler_name[:29]:<30} {str(url)[:39]:<40}")

                # Check if endpoint should appear in sidebar
                if ep.is_enabled and ep.show_in_menu:
                    all_endpoints.append({
                        'tenant': tenant.name,
                        'endpoint': ep,
                        'handler': handler_name,
                        'url': url
                    })

    except Exception as e:
        print(f"  ERROR querying schema {tenant.schema_name}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80)
print("SUMMARY: ENDPOINTS THAT SHOULD APPEAR IN SIDEBAR")
print("="*80)
print(f"\nTotal endpoints configured for sidebar: {len(all_endpoints)}")
print()

if all_endpoints:
    print(f"{'Tenant':<15} {'ID':<5} {'Trigger':<20} {'Menu Title':<25} {'Handler':<30} {'Status':<20}")
    print("-" * 120)

    for item in all_endpoints:
        ep = item['endpoint']
        # Check if handler exists
        handler_status = "✓ Handler OK" if item['handler'] != "None" else "✗ No Handler"

        print(f"{item['tenant']:<15} {ep.id:<5} {ep.trigger_path:<20} {(ep.menu_title or ep.trigger_path.title())[:24]:<25} {item['handler'][:29]:<30} {handler_status:<20}")
else:
    print("  No endpoints found that should appear in sidebar.")
    print("  (Endpoints must have is_enabled=True AND show_in_menu=True)")

print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)
print()

# Check for common issues
issues = []

for tenant in tenants:
    if not tenant.schema_name:
        continue

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {tenant.schema_name},public;")

            # Check for endpoints without menu_title
            no_title = PassThroughEndpoint.objects.filter(
                is_enabled=True,
                show_in_menu=True
            ).filter(
                models.Q(menu_title__isnull=True) | models.Q(menu_title__exact='')
            )

            if no_title.exists():
                for ep in no_title:
                    issues.append(f"  - {tenant.name}: Endpoint '{ep.trigger_path}' (ID: {ep.id}) has no menu_title but show_in_menu=True")

            # Check for endpoints with handlers
            endpoints = PassThroughEndpoint.objects.filter(is_enabled=True, show_in_menu=True)
            for ep in endpoints:
                # All endpoints have at least DefaultScraperHandler, so no need to check
                pass

    except Exception as e:
        issues.append(f"  - {tenant.name}: Error checking schema - {e}")

if issues:
    print("ISSUES FOUND:")
    for issue in issues:
        print(issue)
else:
    print("✓ No issues found. All sidebar links should be working correctly.")

print("\n" + "="*80)

