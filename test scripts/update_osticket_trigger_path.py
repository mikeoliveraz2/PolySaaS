#!/usr/bin/env python
"""
Update OSTicket PassThroughEndpoint trigger_path from /admin/osticket/ to /saas/osticket/
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

# Find OSTicket endpoint
osticket_endpoints = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='osticket'
)

print(f"Found {osticket_endpoints.count()} OSTicket endpoint(s):")
for endpoint in osticket_endpoints:
    print(f"  - ID: {endpoint.id}")
    print(f"    Old trigger_path: {endpoint.trigger_path}")
    print(f"    endpoint_url: {endpoint.endpoint_url}")

    # Update to new path
    if endpoint.trigger_path == '/admin/osticket/':
        endpoint.trigger_path = '/saas/osticket/'
        endpoint.save()
        print(f"    ✓ Updated to: {endpoint.trigger_path}")
    else:
        print(f"    ! No update needed (already different)")
    print()

print("\n✓ Database update complete!")
print("OSTicket is now at: http://127.0.0.1:8000/saas/osticket/")
