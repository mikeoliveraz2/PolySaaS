"""Check where HubSpot TenantApp rows live (public vs olient)."""
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

with connection.cursor() as cur:
    # Check public
    cur.execute("SET search_path TO public")
    cur.execute("""
        SELECT id, tenant_id, app_name, status, extra_config::text
        FROM dose_tenantapp
        WHERE app_name = 'hubspot'
    """)
    rows = cur.fetchall()
    print(f"PUBLIC schema — hubspot TenantApp rows: {len(rows)}")
    for r in rows:
        ec = r[4][:200] if r[4] else '{}'
        print(f"  pk={r[0]} tenant_id={r[1]} status={r[3]}")
        print(f"  extra_config: {ec}")

    # Check olient
    cur.execute("SET search_path TO olient,public")
    cur.execute("""
        SELECT id, tenant_id, app_name, status
        FROM olient.dose_tenantapp
        WHERE app_name = 'hubspot'
    """)
    rows2 = cur.fetchall()
    print(f"\nOLIENT schema — hubspot TenantApp rows: {len(rows2)}")
    for r in rows2:
        print(f"  pk={r[0]} tenant_id={r[1]} status={r[3]}")

    # Check what tenant pk olient maps to
    cur.execute("SET search_path TO public")
    cur.execute("SELECT id, slug, name FROM dose_tenant WHERE slug='olient'")
    t = cur.fetchone()
    print(f"\nTenant 'olient': {t}")
