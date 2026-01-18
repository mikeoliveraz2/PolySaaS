"""
Django management command to copy PassThroughEndpoint data from public to olient schema
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Copy PassThroughEndpoint data from public schema to olient schema'

    def handle(self, *args, **options):
        source_schema = 'public'
        target_schema = 'olient'
        table_name = 'dose_passthroughendpoint'

        self.stdout.write("=" * 80)
        self.stdout.write(f"Copying PassThroughEndpoint data from {source_schema} to {target_schema}")
        self.stdout.write("=" * 80)

        try:
            with connection.cursor() as cursor:
                # Check source
                cursor.execute(f"SET search_path TO {source_schema};")
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                source_count = cursor.fetchone()[0]
                self.stdout.write(f"Source ({source_schema}): {source_count} records")

                if source_count == 0:
                    self.stdout.write(self.style.WARNING(f"No data in {source_schema} schema to copy."))
                    return

                # Check target
                cursor.execute(f"SET search_path TO {target_schema};")
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = %s
                        AND table_name = %s
                    )
                """, [target_schema, table_name])

                if not cursor.fetchone()[0]:
                    self.stdout.write(self.style.ERROR(f"Target table {target_schema}.{table_name} does not exist!"))
                    return

                cursor.execute(f"SELECT COUNT(*) FROM {target_schema}.{table_name}")
                target_count = cursor.fetchone()[0]
                self.stdout.write(f"Target ({target_schema}): {target_count} records")

                if target_count > 0:
                    self.stdout.write(self.style.WARNING(f"Target already has {target_count} records. Use --force to overwrite."))
                    if '--force' not in options:
                        return

                # Get common columns
                cursor.execute(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = %s
                    AND table_name = %s
                    ORDER BY ordinal_position
                """, [target_schema, table_name])
                target_columns = [row[0] for row in cursor.fetchall()]

                cursor.execute(f"SET search_path TO {source_schema};")
                cursor.execute(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = %s
                    AND table_name = %s
                    ORDER BY ordinal_position
                """, [source_schema, table_name])
                source_columns = [row[0] for row in cursor.fetchall()]

                common_columns = [col for col in target_columns if col in source_columns]
                self.stdout.write(f"Common columns: {len(common_columns)}")

                if not common_columns:
                    self.stdout.write(self.style.ERROR("No common columns found!"))
                    return

                # Delete existing data if force
                if target_count > 0 and '--force' in options:
                    cursor.execute(f"DELETE FROM {target_schema}.{table_name}")
                    self.stdout.write(self.style.WARNING(f"Deleted {target_count} existing records"))

                # Copy data
                column_list = ', '.join(common_columns)
                cursor.execute(f"""
                    INSERT INTO {target_schema}.{table_name} ({column_list})
                    SELECT {column_list}
                    FROM {source_schema}.{table_name}
                """)

                rows_copied = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(f"✓ Copied {rows_copied} rows from {source_schema} to {target_schema}"))

                # Show what was copied
                cursor.execute(f"SELECT id, trigger_path, endpoint_url, description FROM {target_schema}.{table_name}")
                rows = cursor.fetchall()
                self.stdout.write("\nCopied records:")
                for row in rows:
                    self.stdout.write(f"  ID {row[0]}: {row[1]} -> {row[2]} ({row[3]})")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())

