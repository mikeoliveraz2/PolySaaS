"""
Drop and recreate a tenant PostgreSQL schema, then run stock Django migrate on it.
Use when a schema was created with the old LIKE-public copy (tables without migration history).

Example:
  python manage.py rebuild_tenant_schema olient --no-input
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands.migrate import Command as DjangoMigrateCommand
from django.db import connection

from dose.management.schema_utils import (
    assert_safe_schema_identifier,
    set_search_path,
    set_search_path_for_migrations,
    tenant_schema_disallowed_reason,
)
from dose.models import Tenant


class Command(BaseCommand):
    help = "DROP SCHEMA CASCADE, CREATE empty schema, apply migrations (stock Django migrate)."

    def add_arguments(self, parser):
        parser.add_argument(
            "schema_name",
            type=str,
            help="PostgreSQL schema name (same as Tenant.schema_name).",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Non-interactive migrate (same as Django --no-input).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow rebuild even if no Tenant row uses this schema_name (dangerous).",
        )

    def handle(self, *args, **options):
        schema_name = options["schema_name"].strip()
        assert_safe_schema_identifier(schema_name)
        if schema_name.lower() == "public":
            raise CommandError("Refusing to rebuild the public schema.")

        reason = tenant_schema_disallowed_reason(schema_name)
        if reason:
            raise CommandError(reason)

        connection.close()
        set_search_path("public")
        exists = Tenant.objects.filter(schema_name=schema_name).exists()
        if not exists and not options["force"]:
            raise CommandError(
                f'No Tenant with schema_name={schema_name!r}. '
                f"Create the tenant first, or pass --force (drops schema anyway)."
            )

        self.stdout.write(self.style.WARNING(f"Dropping schema {schema_name!r} (CASCADE)..."))
        connection.close()
        with connection.cursor() as cursor:
            cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
            cursor.execute(f"CREATE SCHEMA {schema_name}")

        self.stdout.write(self.style.SUCCESS(f"Created empty schema {schema_name!r}. Running migrate..."))
        connection.close()
        set_search_path_for_migrations(schema_name)

        django_cmd = DjangoMigrateCommand(stdout=self.stdout, stderr=self.stderr)
        parser = django_cmd.create_parser("manage.py", "migrate")
        migrate_args = ["--verbosity", str(options.get("verbosity", 1))]
        if options["no_input"]:
            migrate_args.append("--no-input")
        parsed = parser.parse_args(migrate_args)
        opt = vars(parsed).copy()
        # BaseCommand adds keys not used by migrate.handle
        opt.pop("settings", None)
        opt.pop("pythonpath", None)
        opt.pop("traceback", None)
        opt.pop("no_color", None)
        opt.pop("force_color", None)
        opt.pop("skip_checks", None)
        django_cmd.handle(**opt)

        self.stdout.write(
            self.style.SUCCESS(f"Done. Schema {schema_name!r} matches current migrations.")
        )
