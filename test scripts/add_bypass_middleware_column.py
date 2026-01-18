"""
Add bypass_middleware column to PassThroughEndpoint table in all schemas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import Tenant

def add_bypass_middleware_column():
    """Add bypass_middleware column to all schemas"""
    import sys

    schemas = ['public']

    # Get all tenant schemas
    try:
        # First, ensure we're in public schema to query Tenant
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")

        tenants = Tenant.objects.all()
        for tenant in tenants:
            if tenant.schema_name:
                schemas.append(tenant.schema_name)
        sys.stdout.write(f"Found {len(tenants)} tenants\n")
        sys.stdout.flush()
    except Exception as e:
        sys.stdout.write(f"Error getting tenants: {e}\n")
        sys.stdout.flush()

    sys.stdout.write(f"Adding bypass_middleware column to schemas: {schemas}\n")
    sys.stdout.flush()

    for schema in schemas:
        try:
            with connection.cursor() as cursor:
                # Set search_path to the schema we're working with
                cursor.execute(f"SET search_path TO {schema},public;")

                # Check if table exists
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = %s
                        AND table_name = 'dose_passthroughendpoint'
                    )
                """, [schema])

                table_exists = cursor.fetchone()[0]
                if not table_exists:
                    sys.stdout.write(f"  ⚠ Schema '{schema}': Table does not exist, skipping\n")
                    sys.stdout.flush()
                    continue

                # Check if column already exists
                cursor.execute(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = %s
                    AND table_name = 'dose_passthroughendpoint'
                    AND column_name = 'bypass_middleware'
                """, [schema])

                if cursor.fetchone():
                    sys.stdout.write(f"  ✓ Schema '{schema}': Column already exists\n")
                    sys.stdout.flush()
                else:
                    # Add the column
                    cursor.execute(f"""
                        ALTER TABLE {schema}.dose_passthroughendpoint
                        ADD COLUMN bypass_middleware BOOLEAN DEFAULT FALSE NOT NULL
                    """)
                    sys.stdout.write(f"  ✓ Schema '{schema}': Column added successfully\n")
                    sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(f"  ✗ Schema '{schema}': Error - {e}\n")
            sys.stdout.flush()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    add_bypass_middleware_column()
    print("\nDone!")

