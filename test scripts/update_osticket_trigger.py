"""
Update OSTicket endpoint trigger_path to simple name 'osticket'
for new /pt/admin/osticket/ routing format
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from django_tenants.utils import schema_context

# Update in olient schema (your active tenant)
with schema_context('olient'):
    endpoints = PassThroughEndpoint.objects.filter(
        trigger_path__icontains='osticket',
        is_enabled=True
    )

    print(f"Found {endpoints.count()} OSTicket endpoints in olient schema:")
    for ep in endpoints:
        print(f"  Current trigger_path: '{ep.trigger_path}'")
        print(f"  Endpoint URL: {ep.endpoint_url}")

        # Update to simple name
        ep.trigger_path = 'osticket'
        ep.save()
        print(f"  ✓ Updated to: '{ep.trigger_path}'")
        print()

print("Done! OSTicket endpoints updated for /pt/admin/osticket/ routing")
