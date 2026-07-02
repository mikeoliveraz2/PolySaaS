import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

with connection.cursor() as cur:
    # Check what columns exist in olient.dose_tenantapp
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='dose_tenantapp' AND table_schema='olient'
        ORDER BY ordinal_position;
    """)
    cols = [r[0] for r in cur.fetchall()]
    print("olient.dose_tenantapp columns:", cols)

    # List all TenantApps in olient
    cur.execute("SELECT id, app_name, trigger, status, extra_config FROM olient.dose_tenantapp;")
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print(f"  id={r[0]} app_name={r[1]} trigger={r[2]} status={r[3]} extra_config={r[4]}")
    else:
        print("  (no TenantApp rows in olient schema)")

    # Check the tenant record for olient
    cur.execute("SELECT id, name, slug, schema_name FROM public.dose_tenant WHERE slug='olient';")
    t = cur.fetchone()
    print(f"\nTenant: {t}")

    # Check if olient schema has the migration table and what's applied
    cur.execute("""
        SELECT app, name FROM olient.django_migrations
        ORDER BY applied DESC LIMIT 10;
    """)
    migs = cur.fetchall()
    print("\nLatest migrations in olient schema:")
    for m in migs:
        print(f"  {m[0]}.{m[1]}")
