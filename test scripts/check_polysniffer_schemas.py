#!/usr/bin/env python
"""
Check if TrafficLog table exists in all schemas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from django.db import connections

print("="*60)
print("Checking TrafficLog table in all schemas")
print("="*60)
print()

# Check public schema
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'dose_trafficlog'
        );
    """)
    exists = cursor.fetchone()[0]
    print(f"Public schema: {'[OK] TrafficLog table exists' if exists else '[MISSING] TrafficLog table missing'}")

# Check tenant schemas
from dose.models import Tenant

tenants = Tenant.objects.all()
print(f"\nFound {tenants.count()} tenant(s):")

for tenant in tenants:
    schema_name = tenant.schema_name
    print(f"\nChecking schema: {schema_name}")

    # Switch to tenant schema
    with connection.cursor() as cursor:
        # Set search_path to tenant schema
        cursor.execute(f"SET search_path TO {schema_name}, public;")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = %s
                AND table_name = 'dose_trafficlog'
            );
        """, [schema_name])
        exists = cursor.fetchone()[0]
        print(f"  {'[OK] TrafficLog table exists' if exists else '[MISSING] TrafficLog table missing'}")

print()
print("="*60)

