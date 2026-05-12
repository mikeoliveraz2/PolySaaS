#!/usr/bin/env python
"""Copy mmauthtoken from tenant schema TenantApp to public schema TenantApp."""
import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

# Get the token from polysaast15 schema
with connection.cursor() as c:
    c.execute('SET search_path TO "polysaast15"')
    c.execute("SELECT extra_config FROM dose_tenantapp WHERE app_name = 'mattermost' LIMIT 1")
    row = c.fetchone()
    if row and row[0]:
        config = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        token = config.get('mmauthtoken')
        print(f"Found token in polysaast15 schema: {token[:15]}..." if token else "No token found!")
    else:
        print("No TenantApp found in polysaast15!")
        exit(1)

# Update the public schema TenantApp for polysaast15
with connection.cursor() as c:
    c.execute('SET search_path TO "public"')
    c.execute("SELECT id, extra_config FROM dose_tenantapp WHERE app_name = 'mattermost' AND tenant_id = 'polysaast15' LIMIT 1")
    row = c.fetchone()
    if row:
        tid, existing_cfg = row
        cfg = json.loads(existing_cfg) if isinstance(existing_cfg, str) else (existing_cfg or {})
        cfg['mmauthtoken'] = token
        cfg['mmauthtoken_time'] = __import__('time').time()
        c.execute("UPDATE dose_tenantapp SET extra_config = %s WHERE id = %s", [json.dumps(cfg), tid])
        connection.commit()
        print(f"Updated public schema TenantApp ID {tid} with token")
    else:
        print("No public schema TenantApp for polysaast15 found!")
        exit(1)

print("SUCCESS! Token copied to public schema - refresh and test Mattermost")
