"""
Fix OSTicket PassThroughEndpoint URL
Changes endpoint_url from https://oliverenterprises.app.saasify.cloud/scp/dashboard.php
to https://oliverenterprises.app.saasify.cloud/ to fix double /scp/ bug
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

def fix_osticket_endpoint():
    """Update OSTicket PassThroughEndpoint to remove /scp/ from base URL"""

    # Find PassThroughEndpoint with trigger_path containing osticket
    endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='osticket')

    print(f"Found {endpoints.count()} OSTicket endpoint(s)")

    for endpoint in endpoints:
        print(f"\nCurrent endpoint:")
        print(f"  ID: {endpoint.id}")
        print(f"  Trigger Path: {endpoint.trigger_path}")
        print(f"  Endpoint URL: {endpoint.endpoint_url}")
        print(f"  Enabled: {endpoint.is_enabled}")

        # Update to base URL without /scp/
        old_url = endpoint.endpoint_url
        new_url = "https://oliverenterprises.app.saasify.cloud/"

        endpoint.endpoint_url = new_url
        endpoint.save()

        print(f"\n✅ Updated:")
        print(f"  Old: {old_url}")
        print(f"  New: {new_url}")
        print(f"\nNow the middleware will correctly append sub-paths:")
        print(f"  /admin/osticket/scp/login.php -> https://oliverenterprises.app.saasify.cloud/scp/login.php")

if __name__ == '__main__':
    fix_osticket_endpoint()
    print("\n✅ Done! Reload your browser to test login.")
