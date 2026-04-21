#!/usr/bin/env python
"""
Fix contenttypes issue in olient schema and apply TrafficLog migration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("="*60)
print("Fixing contenttypes in olient schema")
print("="*60)
print()

# Set schema to olient
with connection.cursor() as cursor:
    cursor.execute("SET search_path TO olient, public;")

    # Check if django_content_type table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'olient'
            AND table_name = 'django_content_type'
        );
    """)
    table_exists = cursor.fetchone()[0]

    print(f"django_content_type table exists in olient: {table_exists}")

    if table_exists:
        # Check if it has the right structure
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'olient'
            AND table_name = 'django_content_type'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"\nColumns in django_content_type:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")

        # Check if it has data
        cursor.execute("SELECT COUNT(*) FROM olient.django_content_type;")
        count = cursor.fetchone()[0]
        print(f"\nRecords in django_content_type: {count}")

        if count == 0:
            print("\n[INFO] Table exists but is empty - this is fine")
            print("Will try to sync contenttypes...")
        else:
            print("\n[INFO] Table has data - migration should skip it")

    # Check if TrafficLog table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'olient'
            AND table_name = 'dose_trafficlog'
        );
    """)
    trafficlog_exists = cursor.fetchone()[0]

    print(f"\nTrafficLog table exists in olient: {trafficlog_exists}")

    if not trafficlog_exists:
        print("\n[ACTION] Creating TrafficLog table manually...")

        # Get the migration SQL for TrafficLog
        from django.db import migrations
        from dose.polysniffer.models import TrafficLog

        # Create the table using Django's schema editor
        from django.db import models

        # Get the model's fields and create table
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(TrafficLog)

        print("[OK] TrafficLog table created!")
    else:
        print("[OK] TrafficLog table already exists!")

print()
print("="*60)
print("Verifying all schemas...")
print("="*60)

# Check all schemas
schemas = ['public', 'olient']
for schema in schemas:
    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {schema}, public;")
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'dose_trafficlog'
            );
        """)
        exists = cursor.fetchone()[0]
        print(f"{schema}: {'[OK] TrafficLog exists' if exists else '[MISSING] TrafficLog missing'}")

print()
print("="*60)
print("Done!")
print("="*60)

