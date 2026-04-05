#!/usr/bin/env python
"""Test if the stored Mattermost session token is valid."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django
django.setup()

import requests
from django.db import connection
from dose.models import TenantApp, Tenant

tenant = Tenant.objects.get(schema_name='olient')
with connection.cursor() as cur:
    cur.execute('SET search_path TO public;')

ta = TenantApp.objects.filter(tenant=tenant, app_name='mattermost').first()
if not ta or not ta.extra_config:
    print('No TenantApp or extra_config found')
    sys.exit(1)

session_token = ta.extra_config.get('mm_session_token')
if not session_token:
    print('No session token stored')
    sys.exit(1)

print(f'Testing session token: {session_token[:20]}...')

# Test the token against Mattermost /api/v4/users/me
resp = requests.get(
    'http://localhost:8065/api/v4/users/me',
    headers={'Authorization': f'Bearer {session_token}'},
    timeout=10,
)

print(f'Status: {resp.status_code}')
if resp.status_code == 200:
    data = resp.json()
    print(f'Token is VALID - User: {data.get("username")} ({data.get("email")})')
else:
    print(f'Token is INVALID or EXPIRED')
    print(f'Response: {resp.text[:500]}')
    
    # Try to get a fresh token
    print('\nAttempting fresh login...')
    login_id = ta.extra_config.get('mm_login_id')
    password = ta.extra_config.get('mm_password')
    if login_id and password:
        login_resp = requests.post(
            'http://localhost:8065/api/v4/users/login',
            json={'login_id': login_id, 'password': password},
            timeout=10,
        )
        print(f'Login status: {login_resp.status_code}')
        if login_resp.status_code == 200:
            new_token = login_resp.headers.get('Token')
            print(f'New token obtained: {new_token[:20]}...')
            # Update the stored token
            import time
            ta.extra_config['mm_session_token'] = new_token
            ta.extra_config['mm_session_token_time'] = time.time()
            ta.save(update_fields=['extra_config'])
            print('Token updated in database')
        else:
            print(f'Login failed: {login_resp.text[:500]}')
    else:
        print('No login credentials stored')
