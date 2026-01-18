import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

# Set gmail trigger_path back to just "gmail" (no prefix)
endpoint = PassThroughEndpoint.objects.get(id=1)
endpoint.trigger_path = 'gmail'
endpoint.save()

print(f"✅ Updated PassThroughEndpoint:")
print(f"   ID: {endpoint.id}")
print(f"   Trigger Path: {endpoint.trigger_path}")
print(f"   Endpoint URL: {endpoint.endpoint_url}")
print(f"   Provider: {endpoint.provider}")
print("\n✅ Middleware will now match both /admin/gmail/ and /dose/gmail/")
