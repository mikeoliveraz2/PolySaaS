import os, sys
sys.path.insert(0, r'F:\PolySaaS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django; django.setup()

from django.db import connection

with connection.cursor() as cur:
    cur.execute("SET search_path TO public")
    cur.execute("SELECT id, tenant_id, app_name, status FROM dose_tenantapp WHERE app_name = 'hubspot'")
    rows = cur.fetchall()
    print("PUBLIC hubspot TenantApps:", rows)

    try:
        cur.execute("SELECT id, tenant_id, app_name, status FROM olient.dose_tenantapp WHERE app_name = 'hubspot'")
        rows2 = cur.fetchall()
        print("OLIENT hubspot TenantApps:", rows2)
    except Exception as e:
        print("olient query error:", e)

    cur.execute("SELECT * FROM dose_tenant WHERE slug='olient' LIMIT 1")
    cols = [d[0] for d in cur.description]
    t = cur.fetchone()
    print("Tenant olient cols:", cols)
    print("Tenant olient:", t)

# Check via ORM public_bundles
from dose.models import TenantApp, Tenant
with connection.cursor() as cur:
    cur.execute("SET search_path TO public")
tenant = Tenant.objects.filter(slug='olient').first()
print("Tenant obj:", tenant, "pk:", tenant.pk if tenant else None)

ta = TenantApp.public_bundles.filter(tenant=tenant, app_name='hubspot').first()
print("TenantApp via public_bundles:", ta, "pk:", ta.pk if ta else None)
if ta:
    print("  extra_config keys:", list((ta.extra_config or {}).keys()))
    print("  hs_web_cookies present:", bool((ta.extra_config or {}).get('hs_web_cookies')))
