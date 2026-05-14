#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("Fixing trigger_path...")

for schema in ['public', 'polysaast15']:
    with connection.cursor() as c:
        c.execute(f'SET search_path TO "{schema}"')
        c.execute("SELECT id, trigger_path FROM dose_passthroughendpoint WHERE app_name='mattermost' OR trigger_path LIKE '%mattermost%'")
        rows = c.fetchall()
        for rid, path in rows:
            print(f"  {schema}: ID {rid} = '{path}'")
            c.execute("UPDATE dose_passthroughendpoint SET trigger_path='mattermost' WHERE id=%s", [rid])
        connection.commit()

print("\n✅ Fixed! Clear browser cache and reload.")
