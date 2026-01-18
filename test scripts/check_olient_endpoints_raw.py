#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("="*60)
print("Checking olient schema with raw SQL")
print("="*60)
print()

with connection.cursor() as c:
    # Use raw SQL to query directly from olient schema
    c.execute("""
        SELECT id, trigger_path, endpoint_url, passthrough_type, is_enabled, show_in_menu, menu_title
        FROM olient.dose_passthroughendpoint
        ORDER BY id;
    """)
    rows = c.fetchall()
    print(f"Found {len(rows)} endpoints in olient.dose_passthroughendpoint:")
    for row in rows:
        menu_title = row[6] or "(empty)"
        print(f"  ID {row[0]}: trigger_path='{row[1]}', endpoint_url='{row[2]}', type={row[3]}, enabled={row[4]}, show_in_menu={row[5]}, menu_title='{menu_title}'")

    print()
    print("Checking specifically for ID 4:")
    c.execute("""
        SELECT id, trigger_path, endpoint_url, passthrough_type, is_enabled, show_in_menu, menu_title
        FROM olient.dose_passthroughendpoint
        WHERE id = 4;
    """)
    row = c.fetchone()
    if row:
        print(f"  ✅ Found endpoint ID 4:")
        print(f"     trigger_path: '{row[1]}'")
        print(f"     endpoint_url: '{row[2]}'")
        print(f"     passthrough_type: {row[3]}")
        print(f"     is_enabled: {row[4]}")
        print(f"     show_in_menu: {row[5]}")
        menu_title = row[6] or "(empty)"
        print(f"     menu_title: '{menu_title}'")
    else:
        print("  ❌ Endpoint ID 4 NOT FOUND in olient schema")

