import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django
django.setup()

from django.db import connection
from dose.models import Tenant, PassThroughEndpoint

tenant = Tenant.objects.get(slug='polysaas')
with connection.cursor() as cur:
    cur.execute(f'SET search_path TO "{tenant.slug}", public')

print("=== All PassThroughEndpoints ===")
for p in PassThroughEndpoint.objects.all():
    print(f"  {p.trigger_path}: {p.endpoint_url}")

# Fix any wrong Odoo URLs
fixed = 0
for p in PassThroughEndpoint.objects.filter(trigger_path='odoo'):
    if 'odoo2' not in (p.endpoint_url or ''):
        print(f"  FIXING: {p.endpoint_url} -> https://polysaas-odoo2.onrender.com")
        p.endpoint_url = 'https://polysaas-odoo2.onrender.com'
        p.api_endpoint = 'https://polysaas-odoo2.onrender.com/web'
        p.save()
        fixed += 1

print(f"\nFixed {fixed} endpoint(s).")
