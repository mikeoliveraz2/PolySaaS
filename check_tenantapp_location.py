#!/usr/bin/env python
"""Check which schema the TenantApp is actually in."""
import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("Checking for mattermost TenantApp in different schemas...\n")

schemas = ['public', 'polysaast15']

for schema in schemas:
    with connection.cursor() as c:
        c.execute(f'SET search_path TO "{schema}"')
        c.execute("SELECT id, app_name, tenant_id, extra_config FROM dose_tenantapp WHERE app_name = 'mattermost'")
        rows = c.fetchall()
        print(f"Schema '{schema}':")
        if rows:
            for row in rows:
                tid, app, tenant_id, cfg = row
                cfg_parsed = json.loads(cfg) if cfg else {}
                token = cfg_parsed.get('mmauthtoken', 'NOT SET')
                print(f"  ID={tid}, tenant_id={tenant_id}, mmauthtoken={'SET' if token != 'NOT SET' else 'NOT SET'}")
        else:
            print("  No mattermost TenantApp found")
        print()
