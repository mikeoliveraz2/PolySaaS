import os, sys
sys.path.insert(0, r'F:\PolySaaS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django; django.setup()
from django.db import connection
from dose.models import TenantApp, Tenant
with connection.cursor() as cur:
    cur.execute('SET search_path TO public')
t = Tenant.objects.filter(slug='olient').first()
ta = TenantApp.public_bundles.filter(tenant=t, app_name='hubspot').first()
print('hs_hub_subdomain:', (ta.extra_config or {}).get('hs_hub_subdomain'))
print('hs_portal_id:', (ta.extra_config or {}).get('hs_portal_id'))
