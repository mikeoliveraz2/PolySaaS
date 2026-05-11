#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import PassThroughEndpoint

with connection.cursor() as c:
    c.execute('SET search_path TO "polysaast15"')

# Use Django ORM - it handles defaults
endpoint, created = PassThroughEndpoint.objects.update_or_create(
    trigger_path='mattermost',
    defaults={
        'endpoint_url': 'https://polysaas-mattermost.onrender.com',
        'description': 'Mattermost Team Chat - tenant-specific team',
        'is_enabled': True,
        'passthrough_type': 'scraper',
        'integration_mode': 'web_api',
        'api_endpoint': 'https://polysaas-mattermost.onrender.com/api/v4',
        'show_in_menu': True,
        'menu_title': 'Mattermost',
        'menu_icon': 'chat',
        'menu_sort_order': 25,
        'starting_uri': '/',
        'provider': 'render',
    }
)

print(f'{"Created" if created else "Updated"} PassThroughEndpoint: ID {endpoint.id}')
print('REFRESH THE PAGE - Mattermost should appear in sidebar!')
