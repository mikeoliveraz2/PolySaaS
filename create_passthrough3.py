#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

with connection.cursor() as c:
    c.execute('SET search_path TO "polysaast15"')
    
    # Check if exists
    c.execute('SELECT id FROM dose_passthroughendpoint WHERE trigger_path=%s', ['mattermost'])
    existing = c.fetchone()
    
    if existing:
        print(f'PassThroughEndpoint already exists: ID {existing[0]}')
    else:
        # Include provider column
        c.execute('''
            INSERT INTO dose_passthroughendpoint 
            (trigger_path, endpoint_url, description, is_enabled, passthrough_type, 
             integration_mode, api_endpoint, show_in_menu, menu_title, menu_icon, 
             menu_sort_order, starting_uri, provider)
            VALUES (%s, %s, %s, true, 'scraper', 'web_api', %s, true, %s, 'chat', 25, '/', 'render')
        ''', [
            'mattermost',
            'https://polysaas-mattermost.onrender.com',
            'Mattermost Team Chat - tenant-specific team',
            'https://polysaas-mattermost.onrender.com/api/v4',
            'Mattermost'
        ])
        print('Created PassThroughEndpoint for mattermost')
    
    connection.commit()
    print('SUCCESS: Sidebar link should appear now - REFRESH THE PAGE')
