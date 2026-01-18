#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from django.db import connection

with connection.cursor() as c:
    c.execute('SET LOCAL search_path TO olient,public;')
    pt = PassThroughEndpoint.objects.filter(id=4).first()
    if pt:
        print(f"✅ Endpoint ID 4 found:")
        print(f"   trigger_path: '{pt.trigger_path}'")
        print(f"   endpoint_url: '{pt.endpoint_url}'")
        print(f"   passthrough_type: {pt.passthrough_type}")
        print(f"   is_enabled: {pt.is_enabled}")
        print(f"   show_in_menu: {pt.show_in_menu}")
        print(f"   menu_title: '{pt.menu_title}'")
        print()
        print("This endpoint should use GenericScraperPassthroughView")
        print("which calls get_handler() and should find V0PassthroughHandler")
    else:
        print("❌ Endpoint ID 4 NOT FOUND")

