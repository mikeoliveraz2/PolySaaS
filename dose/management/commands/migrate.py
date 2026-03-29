from django.core.management.commands.migrate import Command as DjangoMigrateCommand
from django.db import connection
from dose.models import Tenant
from dose.management.schema_utils import reset_sequences_in_current_schema, set_search_path, set_search_path_for_migrations


class Command(DjangoMigrateCommand):
    help = "Runs Django migrate on public schema, then on every tenant schema (skips reserved names)."

    def handle(self, *args, **options):
        connection.close()
        set_search_path_for_migrations("public")
        self.stdout.write(self.style.SUCCESS("Migrating public schema..."))
        super().handle(*args, **options)
        self.stdout.write(self.style.SUCCESS("[OK] Public schema migrated"))

        connection.close()
        set_search_path("public")
        tenants = Tenant.objects.all().order_by("schema_name")
        tenant_count = tenants.count()

        if tenant_count == 0:
            self.stdout.write(
                self.style.WARNING("No tenants found. Only public schema was migrated.")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"\nFound {tenant_count} tenant row(s). Migrating tenant schemas...")
        )

        for idx, tenant in enumerate(tenants, 1):
            schema = tenant.schema_name
            if not schema:
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipping "{tenant.name}" (ID: {tenant.id}) - no schema_name'
                    )
                )
                continue
            if schema.lower() == "public":
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipping tenant "{tenant.name}" (ID: {tenant.id}) - '
                        f'schema_name "public" is invalid (shared schema, not a tenant)'
                    )
                )
                continue

            self.stdout.write(self.style.WARNING(f"[{idx}/{tenant_count}] Migrating schema: {schema}"))
            connection.close()
            set_search_path_for_migrations(schema)
            try:
                reset_sequences_in_current_schema()
                super().handle(*args, **options)
                self.stdout.write(self.style.SUCCESS(f"  [OK] {schema} migrated"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [FAIL] {schema} error: {e}"))

        self.stdout.write(self.style.SUCCESS("\n[OK] All schemas migrated."))
