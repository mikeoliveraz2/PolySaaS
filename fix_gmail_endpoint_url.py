import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

endpoint = PassThroughEndpoint.objects.get(id=1)
endpoint.endpoint_url = 'https://gmail.googleapis.com/gmail/v1/users/me/'
# Keep provider as 'google' since that's a valid choice
endpoint.save()

print(f"Updated endpoint:")
print(f"  Trigger path: {endpoint.trigger_path}")
print(f"  Endpoint URL: {endpoint.endpoint_url}")
print(f"  Provider: {endpoint.provider}")
