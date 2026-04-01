#!/usr/bin/env python
"""Check which DB schema contains dose_trafficlog"""
import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.db import connection
with connection.cursor() as cur:
    cur.execute("SELECT table_schema FROM information_schema.tables WHERE table_name = 'dose_trafficlog' ORDER BY table_schema;")
    rows = cur.fetchall()
    if rows:
        for r in rows:
            print("schema:", r[0])
    else:
        print("dose_trafficlog NOT FOUND in any schema")
