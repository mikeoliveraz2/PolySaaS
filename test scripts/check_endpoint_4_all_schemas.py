#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from django.db import connection

schemas = ['public', 'olient']

for schema in schemas:
    print(f"=== Checking {schema.upper()} schema ===")
    with connection.cursor() as c:
        c.execute(f'SET LOCAL search_path TO {schema},public;')
        pt = PassThroughEndpoint.objects.filter(id=4).first()
        if pt:
            print(f"✅ Found endpoint ID 4 in {schema} schema:")
            print(f"   trigger_path: '{pt.trigger_path}'")
            print(f"   endpoint_url: '{pt.endpoint_url}'")
            print(f"   passthrough_type: {pt.passthrough_type}")
            print(f"   is_enabled: {pt.is_enabled}")
            print(f"   show_in_menu: {pt.show_in_menu}")
            print(f"   menu_title: '{pt.menu_title}'")
        else:
            print(f"❌ Endpoint ID 4 NOT FOUND in {schema} schema")
    print()

