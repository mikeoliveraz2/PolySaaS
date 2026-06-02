import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, 'D:/PolySaaS')
django.setup()

from django.db import connection
import json

with connection.cursor() as cur:
    cur.execute("SET search_path TO public,pg_catalog")
    cur.execute("SELECT id, app_name, status, tenant_id, extra_config FROM dose_tenantapp WHERE app_name='mattermost'")
    rows = cur.fetchall()
    print(f"Found {len(rows)} mattermost TenantApp rows")
    for row in rows:
        id_, app, status, tenant_id, extra = row
        try:
            cfg = json.loads(extra) if isinstance(extra, str) else (extra or {})
        except Exception as e:
            cfg = {}
            print(f"  JSON error: {e}")
        safe = {k: (str(v)[:12]+'...' if isinstance(v, str) and len(v) > 12 else v) for k,v in cfg.items()}
        print(f"  id={id_} tenant_id={tenant_id} status={status} keys={list(cfg.keys())} preview={safe}")
