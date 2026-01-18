#!/usr/bin/env python
"""
Find v0 endpoint in all schemas, including those without menu_title
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("="*60)
print("Searching for v0 endpoint in ALL schemas")
print("="*60)
print()

schemas_to_check = ['public', 'olient']

for schema in schemas_to_check:
    print(f"=== {schema.upper()} Schema ===")
    with connection.cursor() as c:
        c.execute(f"SET LOCAL search_path TO {schema},public;")
        # Check ALL endpoints, not just ones with menu_title
        c.execute("""
            SELECT id, trigger_path, endpoint_url, passthrough_type, is_enabled, show_in_menu, menu_title
            FROM dose_passthroughendpoint
            WHERE trigger_path ILIKE '%v0%'
               OR endpoint_url ILIKE '%v0%'
               OR menu_title ILIKE '%v0%'
            ORDER BY id;
        """)
        rows = c.fetchall()
        if rows:
            for row in rows:
                print(f"  ✅ FOUND: ID {row[0]}")
                print(f"     trigger_path: '{row[1]}'")
                print(f"     endpoint_url: '{row[2]}'")
                print(f"     passthrough_type: {row[3]}")
                print(f"     is_enabled: {row[4]}")
                print(f"     show_in_menu: {row[5]}")
                print(f"     menu_title: '{row[6] or '(empty)'}'")
        else:
            print("  No v0 endpoints found")

    print()

print("=== Checking ALL endpoints (to see what's actually there) ===")
with connection.cursor() as c:
    c.execute("SET LOCAL search_path TO olient,public;")
    c.execute("""
        SELECT id, trigger_path, endpoint_url, passthrough_type, is_enabled, show_in_menu, menu_title
        FROM dose_passthroughendpoint
        ORDER BY id;
    """)
    rows = c.fetchall()
    print(f"  Total endpoints in olient schema: {len(rows)}")
    for row in rows:
        menu_title = row[6] or "(empty)"
        print(f"    ID {row[0]}: trigger_path='{row[1]}', menu_title='{menu_title}', type={row[3]}")

