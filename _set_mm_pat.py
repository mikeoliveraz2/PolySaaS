"""
One-time script: store Mattermost PAT in TenantApp extra_config for polysaasot.
Run once, then delete this file.  DO NOT COMMIT.
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import json
from django.db import connection

PAT = 'tfbzbw69pjg33cedaegg99hqch'
SCHEMA = 'polysaasot'   # adjust if different

with connection.cursor() as cur:
    cur.execute(f'SET search_path TO "{SCHEMA}", public')
    cur.execute("""
        SELECT id, extra_config
        FROM dose_tenantapp
        WHERE app_name ILIKE '%mattermost%'
        ORDER BY id
        LIMIT 1
    """)
    row = cur.fetchone()
    if not row:
        print("No mattermost TenantApp found in schema:", SCHEMA)
        sys.exit(1)

    pk, cfg_raw = row
    cfg = json.loads(cfg_raw) if cfg_raw else {}
    cfg['mattermost_token'] = PAT
    print(f"Saving to TenantApp id={pk} in schema={SCHEMA}: mattermost_token={PAT[:8]}...")
    cur.execute(
        "UPDATE dose_tenantapp SET extra_config = %s WHERE id = %s",
        [json.dumps(cfg), pk]
    )
    print("Done.")
