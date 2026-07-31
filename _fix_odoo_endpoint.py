import django, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import PassThroughEndpoint, Tenant

TARGET_URL = 'https://polysaas-odoo2.onrender.com'

for t in Tenant.objects.all():
    try:
        with connection.cursor() as c:
            c.execute(f'SET search_path TO "{t.schema_name}"')
        ep = PassThroughEndpoint.objects.filter(slug='odoo').first()
        if ep:
            old = ep.endpoint_url
            ep.endpoint_url = TARGET_URL
            ep.save()
            print(f"[{t.schema_name}] odoo: {old!r} -> {TARGET_URL!r}")
        else:
            print(f"[{t.schema_name}] no odoo endpoint found")
    except Exception as e:
        print(f"[{t.schema_name}] skipped: {e}")
