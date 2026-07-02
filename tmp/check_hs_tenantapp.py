"""Check HubSpot TenantApp state in olient."""
from django.db import connection

with connection.cursor() as cur:
    cur.execute("""
        SELECT id, app_name, status, extra_config
        FROM olient.dose_tenantapp
        WHERE app_name ILIKE '%hubspot%'
           OR (extra_config::text ILIKE '%hubspot%');
    """)
    rows = cur.fetchall()
    print(f"HubSpot TenantApp rows in olient: {len(rows)}")
    for r in rows:
        cfg = r[3] or {}
        if isinstance(cfg, str):
            import json; cfg = json.loads(cfg)
        print(f"  id={r[0]} app_name={r[1]} status={r[2]}")
        print(f"  extra_config keys: {list(cfg.keys())}")

    # Also check public
    cur.execute("""
        SELECT id, app_name, status, extra_config
        FROM public.dose_tenantapp
        WHERE app_name ILIKE '%hubspot%';
    """)
    pub_rows = cur.fetchall()
    print(f"\nHubSpot TenantApp rows in public: {len(pub_rows)}")
    for r in pub_rows:
        cfg = r[3] or {}
        if isinstance(cfg, str):
            import json; cfg = json.loads(cfg)
        print(f"  id={r[0]} app_name={r[1]} status={r[2]}")
        print(f"  extra_config keys: {list(cfg.keys())}")
