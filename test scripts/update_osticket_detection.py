"""
Update OSTicket PassThroughEndpoint to populate auto-detected fields
Extracts base URL and subpaths from endpoint_url
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from urllib.parse import urlparse

def update_osticket_endpoint():
    """Auto-detect and populate base URL and subpaths"""

    endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='osticket')

    print(f"Found {endpoints.count()} OSTicket endpoint(s)\n")

    for endpoint in endpoints:
        print(f"Processing endpoint:")
        print(f"  Trigger Path: {endpoint.trigger_path}")
        print(f"  Endpoint URL: {endpoint.endpoint_url}")

        # Parse the URL
        parsed = urlparse(endpoint.endpoint_url)

        # Base URL = scheme + domain (up to .cloud, .com, etc.)
        detected_base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Subpaths = all segments after domain
        # /scp/dashboard.php -> ['scp', 'dashboard.php']
        path_segments = [seg for seg in parsed.path.strip('/').split('/') if seg]
        detected_subpaths = path_segments if path_segments else []

        print(f"\n  Auto-detected:")
        print(f"    Base URL: {detected_base_url}")
        print(f"    Subpaths: {detected_subpaths}")

        # Update the endpoint
        endpoint.detected_base_url = detected_base_url
        endpoint.detected_subpaths = detected_subpaths
        endpoint.save()

        print(f"\n✅ Updated endpoint with auto-detected values")
        print(f"\nNow middleware can use:")
        print(f"  Base: {detected_base_url}")
        print(f"  Subpath context: {'/'.join(detected_subpaths[:-1]) if len(detected_subpaths) > 1 else 'root'}")

if __name__ == '__main__':
    update_osticket_endpoint()
    print("\n✅ Done! Reload server to use new detection logic.")
