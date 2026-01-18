import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from django.db import connection

# Set schema to olient for tenant-specific endpoints
cursor = connection.cursor()
cursor.execute('SET search_path TO olient, public')

print("Current PassThroughEndpoint configurations (olient schema):")
endpoints = PassThroughEndpoint.objects.all()
for endpoint in endpoints:
    print(f"ID: {endpoint.id}")
    print(f"  trigger_path: {endpoint.trigger_path}")
    print(f"  endpoint_url: {endpoint.endpoint_url}")
    print(f"  passthrough_type: {endpoint.passthrough_type}")
    print(f"  is_enabled: {endpoint.is_enabled}")
    print(f"  tenant_id: {endpoint.tenant_id}")
    print()