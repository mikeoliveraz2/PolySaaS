#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'polysaas.settings')
django.setup()

from dose.models import TenantApp

apps = TenantApp.objects.filter(app_name='mattermost')
print(f"Found {apps.count()} Mattermost TenantApp(s):\n")

for app in apps:
    print(f"ID: {app.id}")
    print(f"  Tenant: {app.tenant.name}")
    print(f"  Status: {app.status}")
    token = app.extra_config.get('mm_token') or app.extra_config.get('mmauthtoken') or 'NONE'
    if token != 'NONE':
        token = token[:20] + '...'
    print(f"  Token: {token}")
    if app.extra_config.get('error'):
        print(f"  Error: {app.extra_config.get('error')}")
    print()
