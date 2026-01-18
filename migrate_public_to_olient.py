#!/usr/bin/env python
"""
Migrate all tenant-specific data from public schema to olient schema.

This script:
1. Copies all data from public schema tables to olient schema
2. Handles foreign key relationships
3. Preserves IDs where possible
4. Logs all operations
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from django.apps import apps
from dose.models import Tenant, PassThroughEndpoint
# MonitorLogger may not exist as a model - check dynamically
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Also use print for immediate output
import sys
def log_print(message):
    print(message, flush=True)
    logger.info(message)

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
    # Add other tenant-specific models here
]

def get_table_name(model_class):
    """Get the actual database table name for a model."""
    return model_class._meta.db_table

def copy_table_data(source_schema, target_schema, table_name):
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
            log_print(f"WARNING: Table {target_schema}.{table_name} does not exist, skipping")
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
            logger.warning(f"No columns found for {target_schema}.{table_name}")
            return 0

        # Check if target table already has data
        cursor.execute(f"SELECT COUNT(*) FROM {target_schema}.{table_name}")
        target_count = cursor.fetchone()[0]

        if target_count > 0:
            log_print(f"Table {target_schema}.{table_name} already has {target_count} rows, skipping copy")
            return target_count

        # Copy data
        column_list = ', '.join(columns)
        log_print(f"Copying data from {source_schema}.{table_name} to {target_schema}.{table_name}...")
        cursor.execute(f"""
            INSERT INTO {target_schema}.{table_name} ({column_list})
            SELECT {column_list}
            FROM {source_schema}.{table_name}
        """)

        rows_copied = cursor.rowcount
        log_print(f"✓ Copied {rows_copied} rows from {source_schema}.{table_name} to {target_schema}.{table_name}")
        return rows_copied

def migrate_data():
    """Main migration function."""
    source_schema = 'public'
    target_schema = 'olient'

    log_print("="*80)
    log_print(f"Starting migration from {source_schema} to {target_schema}")
    log_print("="*80)

    # Verify target schema exists
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.schemata
                WHERE schema_name = %s
            )
        """, [target_schema])

        if not cursor.fetchone()[0]:
            log_print(f"Target schema '{target_schema}' does not exist!")
            log_print("Creating schema...")
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {target_schema};")
            log_print(f"Schema '{target_schema}' created")
        else:
            log_print(f"Target schema '{target_schema}' exists")

    # Get all models
    total_rows = 0
    for model_name in TENANT_SPECIFIC_MODELS:
        try:
            # Try to get model from dose app first
            try:
                model_class = apps.get_model('dose', model_name)
            except:
                # Try other apps
                for app_config in apps.get_app_configs():
                    try:
                        model_class = apps.get_model(app_config.label, model_name)
                        break
                    except:
                        continue
                else:
                    logger.warning(f"Model {model_name} not found, skipping")
                    continue

            table_name = get_table_name(model_class)
            log_print(f"\nMigrating {model_name} ({table_name})...")

            rows = copy_table_data(source_schema, target_schema, table_name)
            total_rows += rows

        except Exception as e:
            logger.error(f"Error migrating {model_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())

    log_print("="*80)
    log_print(f"Migration complete! Total rows copied: {total_rows}")
    log_print("="*80)

    # Verify migration
    log_print("\nVerification:")
    with connection.cursor() as cursor:
        for model_name in TENANT_SPECIFIC_MODELS:
            try:
                model_class = apps.get_model('dose', model_name)
                table_name = get_table_name(model_class)

                cursor.execute(f"SELECT COUNT(*) FROM {source_schema}.{table_name}")
                source_count = cursor.fetchone()[0]

                cursor.execute(f"SELECT COUNT(*) FROM {target_schema}.{table_name}")
                target_count = cursor.fetchone()[0]

                log_print(f"  {model_name}: {source_schema}={source_count}, {target_schema}={target_count}")
            except:
                pass

if __name__ == '__main__':
    try:
        migrate_data()
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
        raise

