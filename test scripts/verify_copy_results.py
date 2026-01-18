#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("="*60)
print("Verifying copy results - key tables")
print("="*60)
print()

key_tables = [
    'dose_passthroughendpoint',
    'socialaccount_socialapp',
    'socialaccount_socialapp_sites',
    'socialaccount_socialtoken',
    'socialaccount_socialaccount',
]

for table_name in key_tables:
    print(f"=== {table_name} ===")
    with connection.cursor() as c:
        # Check public
        c.execute("SET LOCAL search_path TO public;")
        c.execute(f'SELECT COUNT(*) FROM public."{table_name}";')
        public_count = c.fetchone()[0]

        # Check olient
        c.execute("SET LOCAL search_path TO olient,public;")
        c.execute(f'SELECT COUNT(*) FROM olient."{table_name}";')
        olient_count = c.fetchone()[0]

        print(f"  Public: {public_count} records")
        print(f"  Olient: {olient_count} records")
        if public_count == olient_count:
            print(f"  ✅ Match!")
        else:
            print(f"  ⚠️  Mismatch - {abs(public_count - olient_count)} records difference")
    print()

print("="*60)
print("✅ Verification complete")
print("="*60)

