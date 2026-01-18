#!/usr/bin/env python
"""
Check for v0 endpoint in all schemas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("="*60)
print("Checking for v0 endpoint in all schemas")
print("="*60)
print()

# Check public schema
print("=== Public Schema ===")
with connection.cursor() as c:
    c.execute("SET LOCAL search_path TO public;")
    c.execute("SELECT id, trigger_path, endpoint_url, passthrough_type, is_enabled, show_in_menu FROM dose_passthroughendpoint WHERE trigger_path ILIKE '%v0%' OR endpoint_url ILIKE '%v0%';")
    rows = c.fetchall()
    if rows:
        for row in rows:
            print(f"  ID {row[0]}: trigger_path='{row[1]}', endpoint_url='{row[2]}', type={row[3]}, enabled={row[4]}, show_in_menu={row[5]}")
    else:
        print("  No v0 endpoints found")

print()
print("=== Olient Schema ===")
with connection.cursor() as c:
    c.execute("SET LOCAL search_path TO olient,public;")
    c.execute("SELECT id, trigger_path, endpoint_url, passthrough_type, is_enabled, show_in_menu FROM dose_passthroughendpoint WHERE trigger_path ILIKE '%v0%' OR endpoint_url ILIKE '%v0%';")
    rows = c.fetchall()
    if rows:
        for row in rows:
            print(f"  ID {row[0]}: trigger_path='{row[1]}', endpoint_url='{row[2]}', type={row[3]}, enabled={row[4]}, show_in_menu={row[5]}")
    else:
        print("  No v0 endpoints found")

print()
print("=== All endpoints in olient schema ===")
with connection.cursor() as c:
    c.execute("SET LOCAL search_path TO olient,public;")
    c.execute("SELECT id, trigger_path, endpoint_url, passthrough_type, is_enabled, show_in_menu FROM dose_passthroughendpoint ORDER BY id;")
    rows = c.fetchall()
    print(f"  Found {len(rows)} endpoints:")
    for row in rows:
        print(f"    ID {row[0]}: trigger_path='{row[1]}', endpoint_url='{row[2]}', type={row[3]}, enabled={row[4]}, show_in_menu={row[5]}")

