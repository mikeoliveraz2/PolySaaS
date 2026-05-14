#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import TenantApp, Tenant

# Get tenant
t = Tenant.objects.get(schema_name='polysaast15')
print(f'Tenant: {t.name} (schema={t.schema_name})')

# Check for Mattermost TenantApp
with connection.cursor() as c:
    c.execute('SET search_path TO "polysaast15"')
    try:
        ta = TenantApp.objects.filter(app_name='mattermost').first()
        if ta:
            cfg = ta.extra_config or {}
            print(f'TenantApp ID: {ta.id}')
            token = cfg.get('mmauthtoken', 'NOT SET')
            if token != 'NOT SET':
                print(f'mmauthtoken: {token[:20]}...')
            else:
                print('mmauthtoken: NOT SET')
            print(f'mm_user_id: {cfg.get("mm_user_id", "NOT SET")}')
            print(f'mm_team_id: {cfg.get("mm_team_id", "NOT SET")}')
            print(f'mm_login_id: {cfg.get("mm_login_id", "NOT SET")}')
        else:
            print('TenantApp for mattermost NOT FOUND')
    except Exception as e:
        print(f'Error: {e}')
