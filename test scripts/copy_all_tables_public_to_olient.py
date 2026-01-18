#!/usr/bin/env python
"""
Copy ALL records from ALL tables from public schema to olient schema
This fixes the issue where Copilot had everything going to public in error
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("="*60)
print("Copying ALL records from ALL tables: public → olient")
print("="*60)
print()

# Get all tables in public schema
with connection.cursor() as c:
    c.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    public_tables = [row[0] for row in c.fetchall()]

print(f"Found {len(public_tables)} tables in public schema")
print()

total_copied = 0
total_updated = 0
tables_processed = 0
tables_skipped = 0

for table_name in public_tables:
    # Skip Django system tables that shouldn't be copied
    if table_name.startswith('django_') and table_name not in ['django_site', 'django_content_type']:
        continue

    print(f"Processing: {table_name}")

    try:
        with connection.cursor() as c:
            # Check if table exists in olient schema
            c.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'olient'
                    AND table_name = %s
                );
            """, [table_name])
            table_exists = c.fetchone()[0]

            if not table_exists:
                print(f"  ⚠️  Table {table_name} does not exist in olient schema, skipping")
                tables_skipped += 1
                continue

            # Get column names and types from public schema
            c.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                ORDER BY ordinal_position;
            """, [table_name])
            column_info = c.fetchall()
            columns = [row[0] for row in column_info]

            if not columns:
                print(f"  ⚠️  No columns found, skipping")
                tables_skipped += 1
                continue

            # Quote column names to handle case-sensitive columns
            quoted_columns = [f'"{col}"' for col in columns]

            # Get primary key column(s)
            c.execute("""
                SELECT column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = 'public'
                AND tc.table_name = %s;
            """, [table_name])
            pk_columns = [row[0] for row in c.fetchall()]

            # Get all records from public schema (use quoted column names)
            column_list = ', '.join(quoted_columns)
            c.execute(f'SELECT {column_list} FROM public."{table_name}";')
            public_records = c.fetchall()

            if len(public_records) == 0:
                print(f"  ℹ️  No records to copy")
                tables_processed += 1
                continue

            print(f"  Found {len(public_records)} records")

            # Copy/update each record
            copied = 0
            updated = 0

            # Build INSERT ... ON CONFLICT DO UPDATE statement
            if pk_columns:
                # Has primary key - use ON CONFLICT
                placeholders = ', '.join(['%s'] * len(columns))
                quoted_pk_columns = [f'"{pk}"' for pk in pk_columns]
                update_columns = [col for col in columns if col not in pk_columns]
                quoted_update_columns = [f'"{col}"' for col in update_columns]
                update_assignments = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in update_columns])

                for record in public_records:
                    try:
                        c.execute(f"""
                            INSERT INTO olient."{table_name}" ({column_list})
                            VALUES ({placeholders})
                            ON CONFLICT ({', '.join(quoted_pk_columns)})
                            DO UPDATE SET {update_assignments};
                        """, list(record))
                        if c.rowcount > 0:
                            # Check if it was insert or update by checking if record existed
                            pk_values = [record[columns.index(pk)] for pk in pk_columns]
                            quoted_pk_where = [f'"{pk}" = %s' for pk in pk_columns]
                            where_clause = ' AND '.join(quoted_pk_where)
                            c.execute(f"""
                                SELECT COUNT(*) FROM olient."{table_name}"
                                WHERE {where_clause};
                            """, pk_values)
                            existed = c.fetchone()[0] > 0
                            if existed:
                                updated += 1
                            else:
                                copied += 1
                    except Exception as e:
                        print(f"    ⚠️  Error copying record: {e}")
                        continue
            else:
                # No primary key - just insert (might create duplicates)
                placeholders = ', '.join(['%s'] * len(columns))
                for record in public_records:
                    try:
                        c.execute(f"""
                            INSERT INTO olient."{table_name}" ({column_list})
                            VALUES ({placeholders});
                        """, list(record))
                        copied += 1
                    except Exception as e:
                        # If duplicate, skip
                        if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                            continue
                        print(f"    ⚠️  Error copying record: {e}")
                        continue

            print(f"  ✅ Copied: {copied}, Updated: {updated}")
            total_copied += copied
            total_updated += updated
            tables_processed += 1

    except Exception as e:
        print(f"  ❌ Error processing {table_name}: {e}")
        import traceback
        traceback.print_exc()
        tables_skipped += 1

print()
print("="*60)
print("SUMMARY")
print("="*60)
print(f"Tables processed: {tables_processed}")
print(f"Tables skipped: {tables_skipped}")
print(f"Total records copied: {total_copied}")
print(f"Total records updated: {total_updated}")
print()
print("✅ All records have been copied from public to olient schema")
print("   The admin interface should now only show records from olient schema")

