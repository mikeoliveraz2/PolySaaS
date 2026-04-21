#!/usr/bin/env python
"""Quick fix: Add bypass_middleware column to all schemas"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

# Force output
sys.stdout.write("=" * 80 + "\n")
sys.stdout.write("Adding bypass_middleware column to all schemas\n")
sys.stdout.write("=" * 80 + "\n")
sys.stdout.flush()

schemas = ['public', 'olient']  # Add known schemas

for schema in schemas:
    try:
        with connection.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = %s
                    AND table_name = 'dose_passthroughendpoint'
                )
            """, [schema])

            if not cursor.fetchone()[0]:
                sys.stdout.write(f"Schema '{schema}': Table does not exist, skipping\n")
                sys.stdout.flush()
                continue

            # Check if column exists
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s
                AND table_name = 'dose_passthroughendpoint'
                AND column_name = 'bypass_middleware'
            """, [schema])

            if cursor.fetchone():
                sys.stdout.write(f"Schema '{schema}': Column already exists\n")
                sys.stdout.flush()
            else:
                # Add the column
                sys.stdout.write(f"Schema '{schema}': Adding column...\n")
                sys.stdout.flush()
                cursor.execute(f"""
                    ALTER TABLE {schema}.dose_passthroughendpoint
                    ADD COLUMN bypass_middleware BOOLEAN DEFAULT FALSE NOT NULL
                """)
                sys.stdout.write(f"Schema '{schema}': ✓ Column added successfully!\n")
                sys.stdout.flush()
    except Exception as e:
        sys.stdout.write(f"Schema '{schema}': ✗ Error - {e}\n")
        sys.stdout.flush()
        import traceback
        traceback.print_exc()

sys.stdout.write("\nDone! Try accessing the admin page now.\n")
sys.stdout.flush()

