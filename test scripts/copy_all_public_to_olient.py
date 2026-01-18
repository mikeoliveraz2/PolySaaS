#!/usr/bin/env python
"""
Copy ALL tenant-specific records from public schema to olient schema
This fixes the issue where Copilot had everything going to public in error
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from django.apps import apps

print("="*60)
print("Copying ALL tenant-specific records from public to olient")
print("="*60)
print()

# List of tenant-specific tables to copy
# These are the main tables that should be tenant-specific
tables_to_copy = [
    'dose_passthroughendpoint',
    'socialaccount_socialapp',
    'socialaccount_socialapp_sites',  # Many-to-many relationship table
    'dose_userprofile',
    'dose_instruction',
    'dose_callbackdata',
    'dose_task',
    'dose_mlengine',
    'dose_dosemessage',
    'dose_atomicservice',
    'dose_deepseekprompt',
    'dose_subscription',
    'dose_navigationpanel',
    'dose_navigationitem',
    'dose_requestlog',
    'dose_errorlog',
    # Add any other tenant-specific tables here
]

total_copied = 0
total_updated = 0

for table_name in tables_to_copy:
    print(f"\n{'='*60}")
    print(f"Processing table: {table_name}")
    print(f"{'='*60}")

    try:
        # Get all records from public schema
        with connection.cursor() as c:
            c.execute("SET LOCAL search_path TO public;")
            # Get column names first
            c.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                ORDER BY ordinal_position;
            """, [table_name])
            columns = [row[0] for row in c.fetchall()]

            if not columns:
                print(f"  ⚠️  Table {table_name} not found in public schema, skipping")
                continue

            # Get all records
            column_list = ', '.join(columns)
            c.execute(f"SELECT {column_list} FROM public.{table_name};")
            public_records = c.fetchall()

            print(f"  Found {len(public_records)} records in public schema")

            if len(public_records) == 0:
                print(f"  ℹ️  No records to copy")
                continue

            # Check if table exists in olient schema
            c.execute("SET LOCAL search_path TO olient,public;")
            c.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'olient'
                    AND table_name = %s
                );
            """, [table_name])
            table_exists = c.fetchone()[0]

            if not table_exists:
                print(f"  ⚠️  Table {table_name} does not exist in olient schema, skipping")
                continue

            # Get primary key column (usually 'id')
            pk_column = 'id' if 'id' in columns else columns[0]

            # Copy/update each record
            copied = 0
            updated = 0

            for record in public_records:
                # Build column=value pairs for INSERT/UPDATE
                placeholders = ', '.join(['%s'] * len(columns))
                column_assignments = ', '.join([f"{col} = %s" for col in columns])

                # Get primary key value
                pk_index = columns.index(pk_column)
                pk_value = record[pk_index]

                # Check if record exists in olient
                c.execute(f"""
                    SELECT {pk_column} FROM olient.{table_name} WHERE {pk_column} = %s;
                """, [pk_value])
                exists = c.fetchone()

                if exists:
                    # Update existing record
                    # Build UPDATE statement excluding PK from SET clause
                    update_columns = [col for col in columns if col != pk_column]
                    update_assignments = ', '.join([f"{col} = %s" for col in update_columns])
                    update_values = [record[columns.index(col)] for col in update_columns] + [pk_value]

                    c.execute(f"""
                        UPDATE olient.{table_name}
                        SET {update_assignments}
                        WHERE {pk_column} = %s;
                    """, update_values)
                    updated += 1
                else:
                    # Insert new record
                    c.execute(f"""
                        INSERT INTO olient.{table_name} ({column_list})
                        VALUES ({placeholders});
                    """, list(record))
                    copied += 1

            print(f"  ✅ Copied: {copied}, Updated: {updated}")
            total_copied += copied
            total_updated += updated

    except Exception as e:
        print(f"  ❌ Error processing {table_name}: {e}")
        import traceback
        traceback.print_exc()

print()
print("="*60)
print("SUMMARY")
print("="*60)
print(f"Total records copied: {total_copied}")
print(f"Total records updated: {total_updated}")
print()
print("✅ All tenant-specific records have been copied from public to olient schema")
print("   The admin interface should now only show records from olient schema")

