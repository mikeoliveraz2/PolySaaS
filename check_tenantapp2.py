#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

# Raw query to check TenantApp
columns = ['id', 'app_name', 'extra_config']
with connection.cursor() as c:
    c.execute('SET search_path TO "polysaast15"')
    try:
        c.execute('SELECT id, app_name, extra_config FROM dose_tenantapp WHERE app_name=%s', ['mattermost'])
        row = c.fetchone()
        if row:
            print(f'TenantApp found: ID={row[0]}, app_name={row[1]}')
            import json
            cfg = json.loads(row[2]) if row[2] else {}
            token = cfg.get('mmauthtoken', 'NOT SET')
            if token != 'NOT SET':
                print(f'mmauthtoken: {token[:20]}...')
            else:
                print('mmauthtoken: NOT SET')
            print(f'mm_user_id: {cfg.get("mm_user_id", "NOT SET")}')
            print(f'mm_team_id: {cfg.get("mm_team_id", "NOT SET")}')
            print(f'mm_login_id: {cfg.get("mm_login_id", "NOT SET")}')
        else:
            print('TenantApp for mattermost NOT FOUND - need to re-provision')
    except Exception as e:
        print(f'Error: {e}')
