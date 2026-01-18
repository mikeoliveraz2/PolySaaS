"""
Django management command to add bypass_middleware column to all schemas
"""
from django.core.management.base import BaseCommand
from django.db import connection
from dose.models import Tenant


class Command(BaseCommand):
    help = 'Add bypass_middleware column to PassThroughEndpoint in all schemas'

    def handle(self, *args, **options):
        schemas = ['public']

        # Get all tenant schemas
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public;")
            tenants = Tenant.objects.all()
            for tenant in tenants:
                if tenant.schema_name:
                    schemas.append(tenant.schema_name)
            self.stdout.write(self.style.SUCCESS(f'Found {len(tenants)} tenants'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting tenants: {e}'))

        self.stdout.write(f'Processing schemas: {schemas}')

        for schema in schemas:
            try:
                with connection.cursor() as cursor:
                    # Set search_path to the schema we're working with
                    cursor.execute(f"SET search_path TO {schema},public;")

                    # Check if table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = %s
                            AND table_name = 'dose_passthroughendpoint'
                        )
                    """, [schema])

                    table_exists = cursor.fetchone()[0]
                    if not table_exists:
                        self.stdout.write(self.style.WARNING(f"  Schema '{schema}': Table does not exist, skipping"))
                        continue

                    # Check if column already exists
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = %s
                        AND table_name = 'dose_passthroughendpoint'
                        AND column_name = 'bypass_middleware'
                    """, [schema])

                    if cursor.fetchone():
                        self.stdout.write(self.style.SUCCESS(f"  Schema '{schema}': Column already exists"))
                    else:
                        # Add the column
                        cursor.execute(f"""
                            ALTER TABLE {schema}.dose_passthroughendpoint
                            ADD COLUMN bypass_middleware BOOLEAN DEFAULT FALSE NOT NULL
                        """)
                        self.stdout.write(self.style.SUCCESS(f"  Schema '{schema}': Column added successfully"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Schema '{schema}': Error - {e}"))
                import traceback
                self.stdout.write(traceback.format_exc())

        self.stdout.write(self.style.SUCCESS('\nDone!'))

