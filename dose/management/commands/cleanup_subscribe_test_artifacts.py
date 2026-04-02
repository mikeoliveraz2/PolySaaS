"""
Remove a test subscriber user, tenant row, related public data, and DROP the tenant schema.

All ORM work uses search_path public. Safe schema names only (see schema_utils).

Examples:
  python manage.py cleanup_subscribe_test_artifacts --username PSOllie --schema polysaas_llc --no-input
  python manage.py cleanup_subscribe_test_artifacts --dry-run
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from dose.management.schema_utils import assert_safe_schema_identifier, tenant_schema_disallowed_reason
from dose.models import Tenant, TenantApp

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Delete test subscribe artifacts: user, tenant (public row + CASCADE children), "
        "OAuth apps linked to tenant apps, then DROP SCHEMA ... CASCADE."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default="PSOllie",
            help="Django auth username to delete (default: PSOllie).",
        )
        parser.add_argument(
            "--schema",
            default="polysaas_llc",
            help="Tenant PostgreSQL schema_name to drop (default: polysaas_llc).",
        )
        parser.add_argument(
            "--slug",
            default="polysaas-llc",
            help="Tenant slug to match if schema lookup misses (default: polysaas-llc).",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Do not prompt; perform deletions immediately.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be done; do not delete or DROP SCHEMA.",
        )

    def handle(self, *args, **options):
        username = (options["username"] or "").strip()
        schema_name = (options["schema"] or "").strip()
        slug = (options["slug"] or "").strip()
        dry_run = options["dry_run"]

        if not username:
            raise CommandError("--username is required")

        reason = tenant_schema_disallowed_reason(schema_name)
        if reason:
            raise CommandError(reason)
        assert_safe_schema_identifier(schema_name)

        if not options["no_input"] and not dry_run:
            confirm = input(
                f'Type YES to delete user={username!r}, tenant schema={schema_name!r}, '
                f"slug={slug!r}: "
            )
            if confirm != "YES":
                raise CommandError("Aborted.")

        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public, pg_catalog")

        tenant = (
            Tenant.objects.filter(schema_name__iexact=schema_name).first()
            or Tenant.objects.filter(slug__iexact=slug).first()
        )

        user = User.objects.filter(username__iexact=username).first()

        self.stdout.write(f"Tenant row match: {tenant!r}")
        self.stdout.write(f"User match: {user!r} ({getattr(user, 'email', '')})")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes."))
            return

        user_id = user.pk if user else None

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public, pg_catalog")

            if tenant:
                tapps = list(TenantApp.public_bundles.filter(tenant=tenant))
                self.stdout.write(f"Removing OAuth apps for {len(tapps)} TenantApp row(s)…")
                for tapp in tapps:
                    oa = getattr(tapp, "oauth_application", None)
                    if oa is not None:
                        oa.delete()
                    elif getattr(tapp, "oauth_application_id", None):
                        try:
                            from oauth2_provider.models import Application

                            Application.objects.filter(pk=tapp.oauth_application_id).delete()
                        except Exception as exc:
                            self.stdout.write(self.style.WARNING(f"OAuth app delete skipped: {exc}"))

                schema_to_drop = tenant.schema_name or schema_name
                assert_safe_schema_identifier(schema_to_drop)

                if user_id:
                    self._purge_user_id_from_tenant_schema(schema_to_drop, user_id)

                tid = tenant.pk
                tname = tenant.name
                tenant.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Deleted Tenant id={tid} ({tname!r}) and CASCADE public children (subscription, apps, etc.)."
                    )
                )

                with connection.cursor() as cursor:
                    self.stdout.write(
                        self.style.WARNING(f"DROP SCHEMA IF EXISTS {schema_to_drop} CASCADE")
                    )
                    cursor.execute(f"DROP SCHEMA IF EXISTS {schema_to_drop} CASCADE")
            else:
                self.stdout.write(self.style.WARNING("No Tenant row; still attempting schema DROP if present."))
                if user_id:
                    self._purge_user_id_from_tenant_schema(schema_name, user_id)
                with connection.cursor() as cursor:
                    cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")

            if user_id:
                self._strip_djstripe_by_id(user_id)
                with connection.cursor() as cursor:
                    cursor.execute("SET search_path TO public, pg_catalog")
                    self._hard_delete_auth_user_row(cursor, user_id)
                self.stdout.write(self.style.SUCCESS(f"Deleted auth user id={user_id} username={username!r}."))
            else:
                self.stdout.write(self.style.WARNING(f"No user {username!r} to delete."))

        self.stdout.write(self.style.SUCCESS("Cleanup finished."))

    def _purge_user_id_from_tenant_schema(self, schema_name: str, user_id: int) -> None:
        """
        User.delete() issues SET NULL/DELETE against models whose tables live only in
        tenant schemas; Django resolves unqualified names in public and fails.
        Remove user_id rows in the tenant schema first.
        """
        assert_safe_schema_identifier(schema_name)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.columns
                WHERE table_schema = %s AND column_name = 'user_id'
                ORDER BY table_name
                """,
                [schema_name],
            )
            tables = [r[0] for r in cursor.fetchall()]
        for tbl in tables:
            assert_safe_schema_identifier(tbl)
            with connection.cursor() as cursor:
                try:
                    cursor.execute(
                        f'DELETE FROM "{schema_name}"."{tbl}" WHERE user_id = %s',
                        [user_id],
                    )
                    n = cursor.rowcount
                    if n:
                        self.stdout.write(f"  … {schema_name}.{tbl}: deleted {n} row(s) with user_id={user_id}")
                except Exception as exc:
                    self.stdout.write(self.style.WARNING(f"  … skip {schema_name}.{tbl}: {exc}"))

    def _strip_djstripe_by_id(self, user_id: int) -> None:
        try:
            from djstripe.models import Customer, Subscription as DjSubscription

            u = User.objects.filter(pk=user_id).first()
            if not u:
                return
            cust_qs = Customer.objects.filter(subscriber=u)
            for c in cust_qs:
                DjSubscription.objects.filter(customer=c).delete()
            deleted, _ = cust_qs.delete()
            if deleted:
                self.stdout.write(f"Removed {deleted} dj-stripe Customer row(s) for user.")
        except ImportError:
            return

    def _public_fk_columns_referencing_auth_user(self, cursor) -> list[tuple[str, str]]:
        """(table_name, column_name) in public schema for FKs targeting public.auth_user.id."""
        cursor.execute(
            """
            SELECT DISTINCT c.relname::text, a.attname::text
            FROM pg_constraint co
            JOIN pg_class c ON c.oid = co.conrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_class ref ON ref.oid = co.confrelid
            JOIN pg_namespace refn ON refn.oid = ref.relnamespace
            CROSS JOIN unnest(co.conkey, co.confkey) AS u(att_child, att_parent)
            JOIN pg_attribute a ON a.attrelid = co.conrelid AND a.attnum = u.att_child
            JOIN pg_attribute af ON af.attrelid = co.confrelid AND af.attnum = u.att_parent
            WHERE co.contype = 'f'
              AND refn.nspname = 'public'
              AND ref.relname = 'auth_user'
              AND af.attname = 'id'
              AND n.nspname = 'public'
              AND c.relname <> 'auth_user'
            ORDER BY 1, 2
            """
        )
        return [(r[0], r[1]) for r in cursor.fetchall()]

    def _hard_delete_auth_user_row(self, cursor, user_id: int) -> None:
        """
        Delete public.auth_user after removing referencing rows.
        ORM User.delete() is unsafe when tenant-only tables (e.g. dose_trafficlog) are not in public.
        Discover FK children via pg_catalog so new models (e.g. dose_userrequesttracker) are covered.
        """
        pairs = self._public_fk_columns_referencing_auth_user(cursor)
        for round_i in range(30):
            deleted_children = 0
            for relname, attname in pairs:
                assert_safe_schema_identifier(relname)
                assert_safe_schema_identifier(attname)
                cursor.execute(
                    f'DELETE FROM public."{relname}" WHERE "{attname}" = %s',
                    [user_id],
                )
                deleted_children += cursor.rowcount
            cursor.execute("DELETE FROM auth_user WHERE id = %s", [user_id])
            if cursor.rowcount == 1:
                return
            if deleted_children == 0:
                break
            self.stdout.write(
                self.style.NOTICE(
                    f"  … auth_user delete retry round {round_i + 1} (removed {deleted_children} dependent row(s))"
                )
            )
        raise CommandError(
            f"Could not DELETE auth_user id={user_id} after clearing public FK children; "
            "check for composite FKs, non-public references, or manual DB rules."
        )
