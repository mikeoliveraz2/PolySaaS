import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from django_tenants.utils import schema_context

# Update osTicket endpoint in olient schema
with schema_context('olient'):
    endpoint = PassThroughEndpoint.objects.get(trigger_path='osticket')
    endpoint.endpoint_url = 'https://osticket.polysaas.online'
    endpoint.save()
    print(f'✓ Updated osTicket endpoint in olient schema to: {endpoint.endpoint_url}')
    print(f'  Trigger path: {endpoint.trigger_path}')
    print(f'  Menu title: {endpoint.menu_title}')
    print(f'  Is enabled: {endpoint.is_enabled}')
