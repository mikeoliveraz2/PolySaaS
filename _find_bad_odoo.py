import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','mysite.settings')
import django
django.setup()
from django.db import connection
from dose.models import PassThroughEndpoint, Tenant

print("Searching ALL schemas for PassThroughEndpoint with bad odoo URL...")

# Check all tenant schemas
for tenant in Tenant.objects.all():
    with connection.cursor() as cur:
        cur.execute(f'SET search_path TO "{tenant.schema_name}", public')
    pts = PassThroughEndpoint.objects.filter(trigger_path='odoo')
    for pt in pts:
        if 'odoo2' not in pt.endpoint_url:
            print(f"  BAD in {tenant.schema_name}: {pt.endpoint_url}")
        else:
            print(f"  OK  in {tenant.schema_name}: {pt.endpoint_url}")

# Check public
with connection.cursor() as cur:
    cur.execute('SET search_path TO public')
pts = PassThroughEndpoint.objects.filter(trigger_path='odoo')
for pt in pts:
    if 'odoo2' not in pt.endpoint_url:
        print(f"  BAD in public: {pt.endpoint_url}")
    else:
        print(f"  OK  in public: {pt.endpoint_url}")
