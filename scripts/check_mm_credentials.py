#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django
django.setup()

from django.db import connection
from dose.models import TenantApp, Tenant

tenant = Tenant.objects.get(schema_name='olient')
with connection.cursor() as cur:
    cur.execute('SET search_path TO public;')

ta = TenantApp.objects.filter(tenant=tenant, app_name='mattermost').first()
if ta:
    print(f'TenantApp: {ta.app_name} status={ta.status}')
    if ta.extra_config:
        print(f'extra_config keys: {list(ta.extra_config.keys())}')
        print(f'  mm_login_id: {ta.extra_config.get("mm_login_id", "NOT SET")}')
        print(f'  mm_password: {"SET" if ta.extra_config.get("mm_password") else "NOT SET"}')
        print(f'  mm_session_token: {"SET" if ta.extra_config.get("mm_session_token") else "NOT SET"}')
        print(f'  mm_session_token_time: {ta.extra_config.get("mm_session_token_time", "NOT SET")}')
    else:
        print('extra_config is None or empty')
else:
    print('No TenantApp found for mattermost')
