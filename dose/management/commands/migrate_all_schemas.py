from django.core.management.base import BaseCommand
from django.core.management import call_command
from dose.models import Tenant
from django.db import connection

def set_schema(schema_name):
    """Set the PostgreSQL search_path to the specified schema"""
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO {schema_name},public;')

class Command(BaseCommand):
    help = 'Runs makemigrations and migrates ALL schemas for custom multi-tenant setup. Ensures all tenants get all migrations.'

    def handle(self, *args, **options):
        # CRITICAL: Always ensure we're in public schema when querying Tenant model
        set_schema('public')

        self.stdout.write(self.style.SUCCESS('Running makemigrations...'))
        call_command('makemigrations')

        self.stdout.write(self.style.SUCCESS('Migrating public schema...'))
        set_schema('public')
        try:
            call_command('migrate', verbosity=0)
            self.stdout.write(self.style.SUCCESS('✓ Public schema migrated'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Public schema migration error: {e}'))

        # Get all tenants from public schema
        set_schema('public')
        tenants = Tenant.objects.all().order_by('schema_name')
        tenant_count = tenants.count()
        self.stdout.write(self.style.SUCCESS(f'\nFound {tenant_count} tenant(s). Migrating all tenants...'))

        if tenant_count == 0:
            self.stdout.write(self.style.WARNING('No tenants found. Only public schema was migrated.'))
        else:
            for idx, tenant in enumerate(tenants, 1):
                schema_name = tenant.schema_name
                if not schema_name:
                    self.stdout.write(self.style.WARNING(f'Skipping tenant "{tenant.name}" (ID: {tenant.id}) - no schema_name'))
                    continue

                self.stdout.write(self.style.WARNING(f'[{idx}/{tenant_count}] Migrating schema: {schema_name}'))
                set_schema(schema_name)
                try:
                    call_command('migrate', verbosity=0)
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {schema_name} migrated successfully'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ {schema_name} migration error: {e}'))
                    # Continue with other tenants even if one fails

        self.stdout.write(self.style.SUCCESS('\n✓ All migrations completed for all schemas.'))
