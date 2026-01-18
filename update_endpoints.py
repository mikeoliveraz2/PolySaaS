#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to the Python path
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

# Update the endpoints
updates = [
    {
        'trigger': 'nextcloud',
        'endpoint_url': 'http://localhost:8888',
        'is_enabled': True,
        'show_in_menu': True,
    },
    {
        'trigger': 'zammad',
        'endpoint_url': 'http://localhost:8080',
        'is_enabled': True,
        'show_in_menu': True,
    },
    {
        'trigger': 'dolibarr',
        'endpoint_url': 'http://localhost:8889',
        'is_enabled': True,
        'show_in_menu': True,
    },
    {
        'trigger': 'suitecrm',
        'endpoint_url': 'http://localhost:8890',
        'is_enabled': True,
        'show_in_menu': True,
    },
    {
        'trigger': 'odoo',
        'endpoint_url': '',
        'is_enabled': False,
        'show_in_menu': True,
    },
]

for update in updates:
    endpoint, created = PassThroughEndpoint.objects.get_or_create(trigger=update['trigger'], defaults=update)
    if not created:
        for key, value in update.items():
            setattr(endpoint, key, value)
        endpoint.save()
    print(f"Updated {update['trigger']}: {endpoint}")

print("All endpoints updated.")