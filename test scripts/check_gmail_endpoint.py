import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

endpoint = PassThroughEndpoint.objects.get(id=1)
print(f"Trigger path: {endpoint.trigger_path}")
print(f"Endpoint URL: {endpoint.endpoint_url}")
print(f"Provider: {endpoint.provider}")
