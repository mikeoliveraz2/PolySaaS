"""
Fix: Remove mattermost_oidc_enabled=True from all active Mattermost TenantApp extra_config.

This flag was incorrectly set on all tenant records and prevents:
  1. Auto-submit on the PolySaaS login bridge (allow_auto_submit = False)
  2. Credentials prepopulation being effective (form shows but never submits)

The Mattermost instance uses password auth, not OIDC. Removing the flag
restores auto-submit behaviour and the full SSO login bridge flow.
"""
import os, sys, django, json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, 'D:/PolySaaS')
django.setup()

from django.db import connection

updated = 0
skipped = 0

with connection.cursor() as cur:
    cur.execute("SET search_path TO public,pg_catalog")
    cur.execute(
        "SELECT id, tenant_id, extra_config FROM dose_tenantapp WHERE app_name='mattermost' AND status='active'"
    )
    rows = cur.fetchall()
    print(f"Active mattermost TenantApp rows: {len(rows)}")

    for row_id, tenant_id, extra_raw in rows:
        try:
            cfg = json.loads(extra_raw) if isinstance(extra_raw, str) else (extra_raw or {})
        except Exception:
            cfg = {}

        if 'mattermost_oidc_enabled' not in cfg:
            skipped += 1
            continue

        old_val = cfg.pop('mattermost_oidc_enabled')
        new_cfg = json.dumps(cfg)
        cur.execute(
            "UPDATE dose_tenantapp SET extra_config = %s WHERE id = %s",
            [new_cfg, row_id]
        )
        print(f"  Updated id={row_id} tenant={tenant_id}: removed mattermost_oidc_enabled={old_val!r}")
        updated += 1

print(f"\nDone. Updated: {updated}, already clean: {skipped}")
