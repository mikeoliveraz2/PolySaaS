#!/usr/bin/env python
"""
Copy ALL PassThroughEndpoint records from public to olient schema
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("="*60)
print("Copying ALL PassThroughEndpoint records from public to olient")
print("="*60)
print()

# Get all endpoints from public schema
with connection.cursor() as c:
    c.execute("SET LOCAL search_path TO public;")
    c.execute("""
        SELECT id, trigger_path, endpoint_url, passthrough_type, is_enabled,
               show_in_menu, menu_title, menu_icon, description, provider,
               api_auth_type, integration_mode, bypass_middleware, created_at
        FROM public.dose_passthroughendpoint
        ORDER BY id;
    """)
    public_endpoints = c.fetchall()
    print(f"Found {len(public_endpoints)} endpoints in public schema")

# Copy each endpoint to olient schema
copied = 0
updated = 0
with connection.cursor() as c:
    c.execute("SET LOCAL search_path TO olient,public;")

    for row in public_endpoints:
        endpoint_id = row[0]
        trigger_path = row[1]
        endpoint_url = row[2]
        passthrough_type = row[3]
        is_enabled = row[4]
        show_in_menu = row[5]
        menu_title = row[6]
        menu_icon = row[7]
        description = row[8]
        provider = row[9]
        api_auth_type = row[10]
        integration_mode = row[11]
        bypass_middleware = row[12]
        created_at = row[13]

        # Check if endpoint already exists in olient
        c.execute("""
            SELECT id FROM olient.dose_passthroughendpoint WHERE id = %s;
        """, [endpoint_id])
        exists = c.fetchone()

        if exists:
            # Update existing record
            c.execute("""
                UPDATE olient.dose_passthroughendpoint
                SET trigger_path = %s, endpoint_url = %s, passthrough_type = %s,
                    is_enabled = %s, show_in_menu = %s, menu_title = %s,
                    menu_icon = %s, description = %s, provider = %s,
                    api_auth_type = %s, integration_mode = %s, bypass_middleware = %s,
                    created_at = %s
                WHERE id = %s;
            """, [trigger_path, endpoint_url, passthrough_type, is_enabled,
                  show_in_menu, menu_title, menu_icon, description, provider,
                  api_auth_type, integration_mode, bypass_middleware, created_at, endpoint_id])
            updated += 1
            print(f"  ✅ Updated ID {endpoint_id}: {trigger_path}")
        else:
            # Insert new record
            c.execute("""
                INSERT INTO olient.dose_passthroughendpoint
                (id, trigger_path, endpoint_url, passthrough_type, is_enabled,
                 show_in_menu, menu_title, menu_icon, description, provider,
                 api_auth_type, integration_mode, bypass_middleware, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, [endpoint_id, trigger_path, endpoint_url, passthrough_type, is_enabled,
                  show_in_menu, menu_title, menu_icon, description, provider,
                  api_auth_type, integration_mode, bypass_middleware, created_at])
            copied += 1
            print(f"  ✅ Copied ID {endpoint_id}: {trigger_path}")

print()
print("="*60)
print(f"Summary: {copied} copied, {updated} updated")
print("="*60)

