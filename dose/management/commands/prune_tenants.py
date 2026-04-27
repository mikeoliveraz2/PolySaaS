from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dose.management.schema_utils import assert_safe_schema_identifier
from dose.models import Tenant, UserProfile, UserTenantMembership


class Command(BaseCommand):
    help = (
        "Delete all tenants and their schemas except an allowlist. "
        "Deletes Tenant rows + related UserProfile and UserTenantMembership rows, "
        "but does NOT delete auth Users."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep",
            nargs="+",
            default=["olient", "polysaas"],
            help="Tenant slug(s) to keep (default: olient polysaas)",
        )
        parser.add_argument(
            "--no-drop-schemas",
            action="store_true",
            help="Do not drop PostgreSQL schemas; only delete database rows in public schema.",
        )
        parser.add_argument(
            "--yes-i-really-mean-it",
            action="store_true",
            help="Required confirmation flag. Without it, the command will only print what it would do.",
        )

    def handle(self, *args, **options):
        keep_slugs = [str(s).strip() for s in (options.get("keep") or []) if str(s).strip()]
        if not keep_slugs:
            raise CommandError("Refusing to run with empty --keep allowlist.")

        keep_slugs_set = set(keep_slugs)
        for slug in keep_slugs_set:
            assert_safe_schema_identifier(slug.replace("-", "_"))

        tenants_to_keep = list(Tenant.objects.filter(slug__in=keep_slugs_set).order_by("slug"))
        missing_keep = sorted(keep_slugs_set - {t.slug for t in tenants_to_keep})
        if missing_keep:
            raise CommandError(f"Keep tenant(s) not found in database: {', '.join(missing_keep)}")

        tenants_to_delete = list(Tenant.objects.exclude(slug__in=keep_slugs_set).order_by("schema_name"))

        self.stdout.write(self.style.WARNING("Tenant prune plan:"))
        self.stdout.write(self.style.SUCCESS("Keeping tenants:"))
        for t in tenants_to_keep:
            self.stdout.write(self.style.SUCCESS(f"  - {t.slug} (schema={t.schema_name})"))

        if not tenants_to_delete:
            self.stdout.write(self.style.SUCCESS("No other tenants found. Nothing to prune."))
            return

        self.stdout.write(self.style.WARNING("Deleting tenants:"))
        for t in tenants_to_delete:
            self.stdout.write(self.style.WARNING(f"  - {t.slug} (schema={t.schema_name})"))

        if not options.get("yes_i_really_mean_it"):
            self.stdout.write(
                self.style.WARNING(
                    "\nDry-run only. Re-run with --yes-i-really-mean-it to execute deletions."
                )
            )
            return

        # Drop schemas (best-effort)
        if not options.get("no_drop_schemas"):
            for t in tenants_to_delete:
                schema = (t.schema_name or "").strip()
                if not schema:
                    continue
                if schema.lower() == "public":
                    continue
                assert_safe_schema_identifier(schema)

                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT 1 FROM pg_namespace WHERE nspname = %s",
                        [schema],
                    )
                    exists = cursor.fetchone() is not None

                if not exists:
                    self.stdout.write(self.style.WARNING(f"[SKIP] Schema missing: {schema}"))
                    continue

                self.stdout.write(self.style.WARNING(f"Dropping schema {schema!r} (CASCADE)..."))
                connection.close()
                with connection.cursor() as cursor:
                    cursor.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")

        # Delete public-schema rows that reference these tenants
        delete_slugs = [t.slug for t in tenants_to_delete]

        self.stdout.write(self.style.WARNING("Deleting UserTenantMembership rows..."))
        UserTenantMembership.objects.filter(tenant__slug__in=delete_slugs).delete()

        self.stdout.write(self.style.WARNING("Deleting UserProfile rows..."))
        UserProfile.objects.filter(tenant__slug__in=delete_slugs).delete()

        self.stdout.write(self.style.WARNING("Deleting Tenant rows..."))
        Tenant.objects.filter(slug__in=delete_slugs).delete()

        self.stdout.write(self.style.SUCCESS("Done pruning tenants."))
