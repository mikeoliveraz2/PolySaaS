#!/usr/bin/env python
"""
Reverse the PassthroughApp migration (0006) from all tenant schemas.
This handles multi-schema cleanup after deleting the migration file.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import Tenant

def reverse_migration_for_schema(schema_name):
    """Reverse migration 0006 for a specific schema."""
    print(f"\n[REVERSING] Processing schema: {schema_name}")

    try:
        with connection.cursor() as cursor:
            # Switch to the schema
            cursor.execute(f"SET search_path TO {schema_name},public;")

            # Check if the table exists
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = 'dose_passthroughapp'
                )
            """, [schema_name])
            table_exists = cursor.fetchone()[0]

            if table_exists:
                print(f"  ✓ Table dose_passthroughapp exists in {schema_name}")

                # Drop the table
                cursor.execute("DROP TABLE IF EXISTS dose_passthroughapp CASCADE;")
                print(f"  ✓ Dropped dose_passthroughapp table from {schema_name}")

                # Update django_migrations to mark 0006 as unapplied
                cursor.execute(
                    "DELETE FROM django_migrations WHERE app = %s AND name = %s;",
                    ['dose', '0006_add_passthrough_app']
                )
                print(f"  ✓ Removed 0006_add_passthrough_app from django_migrations in {schema_name}")
            else:
                print(f"  ✗ Table dose_passthroughapp does NOT exist in {schema_name} (already reversed?)")

                # Still remove from migrations table if present
                cursor.execute(
                    "SELECT COUNT(*) FROM django_migrations WHERE app = %s AND name = %s;",
                    ['dose', '0006_add_passthrough_app']
                )
                count = cursor.fetchone()[0]
                if count > 0:
                    cursor.execute(
                        "DELETE FROM django_migrations WHERE app = %s AND name = %s;",
                        ['dose', '0006_add_passthrough_app']
                    )
                    print(f"  ✓ Removed stale 0006_add_passthrough_app entry from django_migrations in {schema_name}")
                else:
                    print(f"  ℹ No stale migration entry found")

    except Exception as e:
        print(f"  ✗ ERROR processing {schema_name}: {e}")
        return False

    return True

def main():
    print("=" * 70)
    print("REVERSING PassthroughApp MIGRATION (0006) FROM ALL SCHEMAS")
    print("=" * 70)

    # Get all tenants
    tenants = Tenant.objects.all()
    print(f"\nFound {tenants.count()} tenants to process")

    success_count = 0
    for tenant in tenants:
        if reverse_migration_for_schema(tenant.schema_name):
            success_count += 1

    # Also process public schema just in case
    if reverse_migration_for_schema('public'):
        success_count += 1

    print("\n" + "=" * 70)
    print(f"COMPLETE: Successfully processed {success_count} schemas")
    print("=" * 70)

if __name__ == '__main__':
    main()
