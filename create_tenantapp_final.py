#!/usr/bin/env python
import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

# Config from yesterday's provisioning
config = {
    'mattermost_url': 'https://polysaas-mattermost.onrender.com',
    'mattermost_oidc_enabled': False,
    'mm_token': '8egotznu8fdy3dqsj88tbhwa1r',
    'mmauthtoken': '8egotznu8fdy3dqsj88tbhwa1r',
    'mm_user_id': '6kgu4uec8tgu5j9oyk4jjkspmh',
    'mm_login_id': 'polysaast15',
    'mattermost_username': 'polysaast15',
    'mm_password': 'PolySaaS2026!',
    'mattermost_password': 'PolySaaS2026!',
    'mm_team_id': '4z7w7zxw5fr5bf1rnkwdro1t3o'
}

with connection.cursor() as c:
    c.execute('SET search_path TO "polysaast15"')
    
    # Check if exists
    c.execute('SELECT id FROM dose_tenantapp WHERE app_name=%s', ['mattermost'])
    existing = c.fetchone()
    
    if existing:
        # Update only extra_config
        c.execute('UPDATE dose_tenantapp SET extra_config=%s WHERE app_name=%s',
                  [json.dumps(config), 'mattermost'])
        print(f'Updated TenantApp ID {existing[0]}')
    else:
        # Insert - use schema_name as tenant_id (dose_tenant uses schema_name as PK)
        c.execute('''
            INSERT INTO dose_tenantapp 
            (app_name, app_url, status, extra_config, provisioned_at, tenant_id, last_error)
            VALUES (%s, %s, 'active', %s, NOW(), %s, '')
        ''', ['mattermost', 'https://polysaas-mattermost.onrender.com', json.dumps(config), 'polysaast15'])
        print('Created TenantApp for mattermost')
    
    connection.commit()
    print('Config saved with mmauthtoken: 8egotz...')
