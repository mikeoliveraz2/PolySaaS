"""
Copy PassThroughEndpoint data from public schema to olient schema
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
import sys

def copy_passthrough_endpoints():
    """Copy PassThroughEndpoint data from public to olient schema"""

    source_schema = 'public'
    target_schema = 'olient'
    table_name = 'dose_passthroughendpoint'

    sys.stdout.write("=" * 80 + "\n")
    sys.stdout.write(f"Copying PassThroughEndpoint data from {source_schema} to {target_schema}\n")
    sys.stdout.write("=" * 80 + "\n")
    sys.stdout.flush()

    try:
        with connection.cursor() as cursor:
            # Check if source table has data
            cursor.execute(f"SET search_path TO {source_schema};")
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            source_count = cursor.fetchone()[0]
            sys.stdout.write(f"Source ({source_schema}): {source_count} records\n")
            sys.stdout.flush()

            if source_count == 0:
                sys.stdout.write(f"No data in {source_schema} schema to copy.\n")
                sys.stdout.flush()
                return

            # Check if target table exists and has data
            cursor.execute(f"SET search_path TO {target_schema};")
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = %s
                    AND table_name = %s
                )
            """, [target_schema, table_name])

            if not cursor.fetchone()[0]:
                sys.stdout.write(f"Target table {target_schema}.{table_name} does not exist!\n")
                sys.stdout.flush()
                return

            cursor.execute(f"SELECT COUNT(*) FROM {target_schema}.{table_name}")
            target_count = cursor.fetchone()[0]
            sys.stdout.write(f"Target ({target_schema}): {target_count} records\n")
            sys.stdout.flush()

            if target_count > 0:
                sys.stdout.write(f"Target already has {target_count} records. Skipping copy.\n")
                sys.stdout.flush()
                return

            # Get column names from target schema (to ensure we copy to correct structure)
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s
                AND table_name = %s
                ORDER BY ordinal_position
            """, [target_schema, table_name])

            target_columns = [row[0] for row in cursor.fetchall()]
            sys.stdout.write(f"Target columns: {', '.join(target_columns)}\n")
            sys.stdout.flush()

            # Get column names from source schema
            cursor.execute(f"SET search_path TO {source_schema};")
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s
                AND table_name = %s
                ORDER BY ordinal_position
            """, [source_schema, table_name])

            source_columns = [row[0] for row in cursor.fetchall()]
            sys.stdout.write(f"Source columns: {', '.join(source_columns)}\n")
            sys.stdout.flush()

            # Find common columns (columns that exist in both schemas)
            common_columns = [col for col in target_columns if col in source_columns]
            sys.stdout.write(f"Common columns: {', '.join(common_columns)}\n")
            sys.stdout.flush()

            if not common_columns:
                sys.stdout.write("No common columns found! Cannot copy data.\n")
                sys.stdout.flush()
                return

            # Copy data
            column_list = ', '.join(common_columns)
            sys.stdout.write(f"\nCopying data...\n")
            sys.stdout.flush()

            cursor.execute(f"""
                INSERT INTO {target_schema}.{table_name} ({column_list})
                SELECT {column_list}
                FROM {source_schema}.{table_name}
            """)

            rows_copied = cursor.rowcount
            sys.stdout.write(f"[SUCCESS] Copied {rows_copied} rows from {source_schema} to {target_schema}\n")
            sys.stdout.flush()

            # Verify
            cursor.execute(f"SELECT COUNT(*) FROM {target_schema}.{table_name}")
            final_count = cursor.fetchone()[0]
            sys.stdout.write(f"\nVerification: {target_schema} now has {final_count} records\n")
            sys.stdout.flush()

            # Show what was copied
            cursor.execute(f"SELECT id, trigger_path, endpoint_url, description FROM {target_schema}.{table_name}")
            rows = cursor.fetchall()
            sys.stdout.write(f"\nCopied records:\n")
            for row in rows:
                sys.stdout.write(f"  ID {row[0]}: {row[1]} -> {row[2]} ({row[3]})\n")
            sys.stdout.flush()

    except Exception as e:
        sys.stdout.write(f"[ERROR] Error: {e}\n")
        sys.stdout.flush()
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    copy_passthrough_endpoints()
    sys.stdout.write("\nDone!\n")
    sys.stdout.flush()

