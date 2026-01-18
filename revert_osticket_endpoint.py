"""
Revert OSTicket PassThroughEndpoint URL back to original
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='osticket')

print(f"Found {endpoints.count()} OSTicket endpoint(s)")

for endpoint in endpoints:
    print(f"\nCurrent endpoint:")
    print(f"  Trigger Path: {endpoint.trigger_path}")
    print(f"  Endpoint URL: {endpoint.endpoint_url}")

    # Revert to original
    endpoint.endpoint_url = "https://oliverenterprises.app.saasify.cloud/scp/dashboard.php"
    endpoint.save()

    print(f"\n✅ Reverted to: {endpoint.endpoint_url}")

print("\n✅ Done!")
