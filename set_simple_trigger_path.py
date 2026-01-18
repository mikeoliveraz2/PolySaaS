import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

# Set Gmail endpoint to simple trigger_path
gmail_endpoint = PassThroughEndpoint.objects.get(id=1)
print(f"Current path: {gmail_endpoint.trigger_path}")

gmail_endpoint.trigger_path = 'gmail'
gmail_endpoint.save()

print(f"✅ Updated path: {gmail_endpoint.trigger_path}")
print("Middleware will now match both /admin/gmail/ and /dose/gmail/")
