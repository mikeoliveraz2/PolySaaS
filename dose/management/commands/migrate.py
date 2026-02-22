from django.core.management.commands.migrate import Command as DjangoMigrateCommand
from django.db import connection
from dose.models import Tenant


def set_schema(schema_name):
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO {schema_name},public;')


class Command(DjangoMigrateCommand):
    help = 'Runs Django migrate on public schema, then on every tenant schema automatically.'

    def handle(self, *args, **options):
        set_schema('public')
        self.stdout.write(self.style.SUCCESS('Migrating public schema...'))
        super().handle(*args, **options)
        self.stdout.write(self.style.SUCCESS('✓ Public schema migrated'))

        set_schema('public')
        tenants = Tenant.objects.all().order_by('schema_name')
        tenant_count = tenants.count()

        if tenant_count == 0:
            self.stdout.write(self.style.WARNING('No tenants found. Only public schema was migrated.'))
            return

        self.stdout.write(self.style.SUCCESS(f'\nFound {tenant_count} tenant(s). Migrating all...'))

        for idx, tenant in enumerate(tenants, 1):
            schema = tenant.schema_name
            if not schema:
                self.stdout.write(self.style.WARNING(
                    f'Skipping "{tenant.name}" (ID: {tenant.id}) — no schema_name'))
                continue

            self.stdout.write(self.style.WARNING(
                f'[{idx}/{tenant_count}] Migrating schema: {schema}'))
            set_schema(schema)
            try:
                super().handle(*args, **options)
                self.stdout.write(self.style.SUCCESS(f'  ✓ {schema} migrated'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ {schema} error: {e}'))

        self.stdout.write(self.style.SUCCESS('\n✓ All schemas migrated.'))
