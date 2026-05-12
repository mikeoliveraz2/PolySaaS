#!/usr/bin/env python
"""
Copy PassThroughEndpoint templates from PUBLIC to tenant schema.
Used during tenant provisioning.
"""
import os, django, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import PassThroughEndpoint

TENANT_SCHEMA = 'polysaast15'  # Target tenant
APPS_TO_COPY = ['mattermost']  # Apps to provision

print(f'Copying endpoints from PUBLIC to {TENANT_SCHEMA}...')

# Get templates from public
public_endpoints = {}
with connection.cursor() as c:
    c.execute('SET search_path TO "public"')
    
for template in PassThroughEndpoint.objects.filter(trigger_path__in=APPS_TO_COPY):
    public_endpoints[template.trigger_path] = template
    print(f'  Found template: {template.trigger_path}')

# Copy to tenant schema
with connection.cursor() as c:
    c.execute(f'SET search_path TO "{TENANT_SCHEMA}"')
    
for trigger_path, template in public_endpoints.items():
    # Check if exists in tenant
    existing = PassThroughEndpoint.objects.filter(trigger_path=trigger_path).first()
    
    if existing:
        print(f'  Already exists in tenant: {trigger_path} (ID: {existing.id})')
    else:
        # Create copy
        new_endpoint = PassThroughEndpoint.objects.create(
            trigger_path=template.trigger_path,
            endpoint_url=template.endpoint_url,
            description=template.description,
            is_enabled=True,
            passthrough_type=template.passthrough_type,
            integration_mode=template.integration_mode,
            api_endpoint=template.api_endpoint,
            show_in_menu=True,
            menu_title=template.menu_title,
            menu_icon=template.menu_icon,
            menu_sort_order=template.menu_sort_order,
            starting_uri=template.starting_uri,
            provider='custom',
        )
        print(f'  Created in tenant: {trigger_path} (ID: {new_endpoint.id})')

print(f'\nEndpoints copied to {TENANT_SCHEMA}!')
print('Refresh the page - sidebar links should appear.')
