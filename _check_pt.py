import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django
django.setup()

from django.db import connection
from dose.models import Tenant, PassThroughEndpoint

tenant = Tenant.objects.get(slug='polysaas')
with connection.cursor() as cur:
    cur.execute(f'SET search_path TO "{tenant.slug}", public')

pts = PassThroughEndpoint.objects.filter(trigger_path__in=['odoo','mattermost'])
for p in pts:
    print(f"{p.trigger_path}: endpoint_url={p.endpoint_url} | api_endpoint={p.api_endpoint}")
