"""List PassThroughEndpoint rows in olient vs public."""
import os, sys
sys.path.insert(0, r'F:\PolySaaS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django; django.setup()

from django.db import connection

def list_eps(schema):
    with connection.cursor() as cur:
        cur.execute(f'SET search_path TO "{schema}",public')
        cur.execute("""
            SELECT id, menu_title, slug, endpoint_url, is_enabled, show_in_menu, starting_uri
            FROM dose_passthroughendpoint
            ORDER BY id
        """)
        rows = cur.fetchall()
    print(f"\n=== {schema}.dose_passthroughendpoint ({len(rows)} rows) ===")
    for r in rows:
        print(f"  id={r[0]} title={r[1]!r} slug={r[2]!r} enabled={r[4]} menu={r[5]} starting_uri={r[6]!r}")
        print(f"       url={r[3]!r}")

list_eps('olient')
list_eps('public')

# TenantApp in public for olient
with connection.cursor() as cur:
    cur.execute("SET search_path TO public")
    cur.execute("""
        SELECT id, tenant_id, app_name, status
        FROM dose_tenantapp
        WHERE tenant_id = 'olient'
        ORDER BY app_name
    """)
    print("\n=== public.dose_tenantapp for olient ===")
    for r in cur.fetchall():
        print(f"  id={r[0]} app={r[2]} status={r[3]}")
