"""
REVERT OSTicket PassThroughEndpoint URL back to original
Changes endpoint_url from https://oliverenterprises.app.saasify.cloud/
back to https://oliverenterprises.app.saasify.cloud/scp/dashboard.php
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

def revert_osticket_endpoint():
    """Revert OSTicket PassThroughEndpoint to original URL"""

    endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='osticket')

    print(f"Found {endpoints.count()} OSTicket endpoint(s)")

    for endpoint in endpoints:
        print(f"\nCurrent endpoint:")
        print(f"  ID: {endpoint.id}")
        print(f"  Trigger Path: {endpoint.trigger_path}")
        print(f"  Endpoint URL: {endpoint.endpoint_url}")

        # Revert to original URL
        old_url = endpoint.endpoint_url
        original_url = "https://oliverenterprises.app.saasify.cloud/scp/dashboard.php"

        endpoint.endpoint_url = original_url
        endpoint.save()

        print(f"\n✅ REVERTED:")
        print(f"  From: {old_url}")
        print(f"  To: {original_url}")

if __name__ == '__main__':
    revert_osticket_endpoint()
    print("\n✅ Database reverted to original URL.")
