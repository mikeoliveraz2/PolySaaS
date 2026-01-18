"""
Update existing PassThroughEndpoint records with correct passthrough_type and bypass_middleware
Run this after the migration: python update_passthrough_config.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

def update_passthrough_endpoints():
    """Update existing PassThroughEndpoint records"""

    # Find Gmail endpoint(s)
    gmail_endpoints = PassThroughEndpoint.objects.filter(
        trigger_path__icontains='gmail'
    )

    for endpoint in gmail_endpoints:
        endpoint.passthrough_type = 'api'
        endpoint.bypass_middleware = True
        endpoint.save()
        print(f"✅ Updated Gmail endpoint: {endpoint.trigger_path} -> passthrough_type='api', bypass_middleware=True")

    # Find OSTicket endpoint(s)
    osticket_endpoints = PassThroughEndpoint.objects.filter(
        trigger_path__icontains='osticket'
    )

    for endpoint in osticket_endpoints:
        endpoint.passthrough_type = 'scraper'
        endpoint.bypass_middleware = True
        endpoint.save()
        print(f"✅ Updated OSTicket endpoint: {endpoint.trigger_path} -> passthrough_type='scraper', bypass_middleware=True")

    # List all endpoints for verification
    print("\n📋 All PassThroughEndpoint records:")
    for endpoint in PassThroughEndpoint.objects.all():
        print(f"  - {endpoint.trigger_path}: type={endpoint.passthrough_type}, bypass={endpoint.bypass_middleware}, enabled={endpoint.is_enabled}")

if __name__ == '__main__':
    update_passthrough_endpoints()
