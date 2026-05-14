#!/usr/bin/env python
"""Fix the trigger_path for mattermost endpoint."""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("Fixing mattermost endpoint trigger_path...")

with connection.cursor() as c:
    # Fix in public schema (template)
    c.execute('SET search_path TO "public"')
    c.execute("UPDATE dose_passthroughendpoint SET trigger_path = 'mattermost' WHERE trigger_path LIKE '%mattermost%'")
    print(f"  Updated public schema: {c.rowcount} rows")
    
    # Fix in tenant schema
    c.execute('SET search_path TO "polysaast15"')
    c.execute("UPDATE dose_passthroughendpoint SET trigger_path = 'mattermost' WHERE trigger_path LIKE '%mattermost%'")
    print(f"  Updated polysaast15 schema: {c.rowcount} rows")
    
    connection.commit()

print("\n✅ Fixed! trigger_path is now 'mattermost'")
print("Clear browser cache and test again - URLs should now be /pt/admin/mattermost/...")
