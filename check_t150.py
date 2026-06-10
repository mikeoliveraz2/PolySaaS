#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dose.settings')
django.setup()

from dose.models import User, Tenant, TenantApp

# Test t150
try:
    u = User.objects.get(username='polysaast150')
    t = u.tenant
    print(f'User: {u.username}')
    print(f'Tenant: {t.name} ({t.schema})')
    
    # Check for Mattermost TenantApp
    ta = TenantApp.objects.filter(tenant=t, app_name='mattermost').first()
    if ta:
        print(f'TenantApp ID: {ta.id}')
        print(f'Status: {ta.status}')
        print(f'Extra config keys: {list(ta.extra_config.keys()) if ta.extra_config else "None"}')
        if ta.extra_config:
            print(f'  - mm_token: {"yes" if ta.extra_config.get("mm_token") else "no"}')
            print(f'  - mm_user_id: {ta.extra_config.get("mm_user_id", "not set")}')
            print(f'  - mm_username: {ta.extra_config.get("mm_username", "not set")}')
except Exception as e:
    print(f'Error: {e}')
