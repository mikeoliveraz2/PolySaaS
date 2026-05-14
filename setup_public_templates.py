#!/usr/bin/env python
"""
Setup template PassThroughEndpoints in PUBLIC schema.
These serve as templates that get copied to tenant schemas during provisioning.
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import PassThroughEndpoint

# Template configs for bundled apps
TEMPLATES = {
    'mattermost': {
        'endpoint_url': 'https://polysaas-mattermost.onrender.com',
        'description': 'Mattermost Team Chat - tenant-specific team',
        'passthrough_type': 'scraper',
        'integration_mode': 'web_api',
        'api_endpoint': 'https://polysaas-mattermost.onrender.com/api/v4',
        'menu_icon': 'chat',
        'menu_sort_order': 25,
        'provider': 'custom',
    },
    'odoo': {
        'endpoint_url': 'https://polysaas-odoo.onrender.com',
        'description': 'Odoo ERP - tenant-specific database',
        'passthrough_type': 'scraper',
        'integration_mode': 'web_api',
        'api_endpoint': 'https://polysaas-odoo.onrender.com/api/v2',
        'menu_icon': 'business',
        'menu_sort_order': 20,
        'provider': 'custom',
    },
    'nextcloud': {
        'endpoint_url': 'https://polysaas-nextcloud.onrender.com',
        'description': 'NextCloud File Storage - tenant-specific',
        'passthrough_type': 'scraper',
        'integration_mode': 'web_api',
        'api_endpoint': 'https://polysaas-nextcloud.onrender.com/api/v1',
        'menu_icon': 'cloud',
        'menu_sort_order': 30,
        'provider': 'custom',
    },
}

print('Setting up template endpoints in PUBLIC schema...')

with connection.cursor() as c:
    c.execute('SET search_path TO "public"')

for trigger_path, config in TEMPLATES.items():
    endpoint, created = PassThroughEndpoint.objects.update_or_create(
        trigger_path=trigger_path,
        defaults={
            'endpoint_url': config['endpoint_url'],
            'description': config['description'],
            'is_enabled': True,
            'passthrough_type': config['passthrough_type'],
            'integration_mode': config['integration_mode'],
            'api_endpoint': config['api_endpoint'],
            'show_in_menu': True,
            'menu_title': trigger_path.title(),
            'menu_icon': config['menu_icon'],
            'menu_sort_order': config['menu_sort_order'],
            'starting_uri': '/',
            'provider': config['provider'],
        }
    )
    action = 'Created' if created else 'Updated'
    print(f'  {action} template: {trigger_path} (ID: {endpoint.id})')

print('\nTemplate endpoints ready in PUBLIC schema!')
print('These will be copied to tenant schemas during provisioning.')
