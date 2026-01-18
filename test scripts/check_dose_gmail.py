import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("=== All Gmail PassThroughEndpoints ===")
gmail_endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='gmail')
for ep in gmail_endpoints:
    print(f"\nID: {ep.id}")
    print(f"  Trigger path: {ep.trigger_path}")
    print(f"  Endpoint URL: {ep.endpoint_url}")
    print(f"  Provider: {ep.provider}")
    print(f"  Enabled: {ep.is_enabled}")
    print(f"  Bypass middleware: {ep.bypass_middleware}")
