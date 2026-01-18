"""
Django management command to migrate data from public schema to olient schema.
Run with: python manage.py migrate_public_to_olient
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps
import logging

logger = logging.getLogger(__name__)

# Models that should be tenant-specific (exclude Tenant itself)
TENANT_SPECIFIC_MODELS = [
    'PassThroughEndpoint',
    'MonitorLogger',
    'CallbackData',
    'Instruction',
    'Task',
    'NavigationPanel',
    'NavigationItem',
    'DashboardButton',
    'DoseMessage',
    'UserProfile',
]

class Command(BaseCommand):
    help = 'Migrate all tenant-specific data from public schema to olient schema'

    def handle(self, *args, **options):
        source_schema = 'public'
        target_schema = 'olient'

        self.stdout.write("="*80)
        self.stdout.write(self.style.SUCCESS(f"Starting migration from {source_schema} to {target_schema}"))
        self.stdout.write("="*80)

        # Verify target schema exists
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.schemata
                    WHERE schema_name = %s
                )
            """, [target_schema])

            if not cursor.fetchone()[0]:
                self.stdout.write(self.style.WARNING(f"Target schema '{target_schema}' does not exist!"))
                self.stdout.write("Creating schema...")
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {target_schema};")
                self.stdout.write(self.style.SUCCESS(f"Schema '{target_schema}' created"))
            else:
                self.stdout.write(f"Target schema '{target_schema}' exists")

        # Get all models and migrate
        total_rows = 0
        for model_name in TENANT_SPECIFIC_MODELS:
            try:
                # Try to get model from dose app first
                try:
                    model_class = apps.get_model('dose', model_name)
                except:
                    # Try other apps
                    model_class = None
                    for app_config in apps.get_app_configs():
                        try:
                            model_class = apps.get_model(app_config.label, model_name)
                            break
                        except:
                            continue

                    if not model_class:
                        self.stdout.write(self.style.WARNING(f"Model {model_name} not found, skipping"))
                        continue

                table_name = model_class._meta.db_table
                self.stdout.write(f"\nMigrating {model_name} ({table_name})...")

                rows = self.copy_table_data(source_schema, target_schema, table_name)
                total_rows += rows

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error migrating {model_name}: {e}"))
                import traceback
                self.stdout.write(traceback.format_exc())

        self.stdout.write("="*80)
        self.stdout.write(self.style.SUCCESS(f"Migration complete! Total rows copied: {total_rows}"))
        self.stdout.write("="*80)

        # Verify migration
        self.stdout.write("\nVerification:")
        with connection.cursor() as cursor:
            for model_name in TENANT_SPECIFIC_MODELS:
                try:
                    model_class = apps.get_model('dose', model_name)
                    table_name = model_class._meta.db_table

                    cursor.execute(f"SELECT COUNT(*) FROM {source_schema}.{table_name}")
                    source_count = cursor.fetchone()[0]

                    cursor.execute(f"SELECT COUNT(*) FROM {target_schema}.{table_name}")
                    target_count = cursor.fetchone()[0]

                    self.stdout.write(f"  {model_name}: {source_schema}={source_count}, {target_schema}={target_count}")
                except:
                    pass

    def copy_table_data(self, source_schema, target_schema, table_name):
        """Copy all data from source schema table to target schema table."""
        with connection.cursor() as cursor:
            # Check if table exists in target schema
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = %s
                )
            """, [target_schema, table_name])

            if not cursor.fetchone()[0]:
                self.stdout.write(self.style.WARNING(f"Table {target_schema}.{table_name} does not exist, skipping"))
                return 0

            # Get column names
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, [target_schema, table_name])

            columns = [row[0] for row in cursor.fetchall()]
            if not columns:
                self.stdout.write(self.style.WARNING(f"No columns found for {target_schema}.{table_name}"))
                return 0

            # Check if target table already has data
            cursor.execute(f"SELECT COUNT(*) FROM {target_schema}.{table_name}")
            target_count = cursor.fetchone()[0]

            if target_count > 0:
                self.stdout.write(f"Table {target_schema}.{table_name} already has {target_count} rows, skipping copy")
                return target_count

            # Copy data
            column_list = ', '.join(columns)
            self.stdout.write(f"Copying data from {source_schema}.{table_name} to {target_schema}.{table_name}...")
            cursor.execute(f"""
                INSERT INTO {target_schema}.{table_name} ({column_list})
                SELECT {column_list}
                FROM {source_schema}.{table_name}
            """)

            rows_copied = cursor.rowcount
            self.stdout.write(self.style.SUCCESS(f"✓ Copied {rows_copied} rows from {source_schema}.{table_name} to {target_schema}.{table_name}"))
            return rows_copied

