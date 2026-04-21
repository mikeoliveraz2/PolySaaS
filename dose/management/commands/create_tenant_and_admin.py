"""
Create a tenant (PostgreSQL schema + row in public) and a tenant admin user.

After a *new* tenant row is saved, runs ``migrate_all_schemas`` so the new schema
gets the same tables as other tenants (project convention).

Typical usage::

    python manage.py create_tenant_and_admin \\
        --tenant-name "Acme Corp" \\
        --slug acme \\
        --admin-username acme_admin \\
        --admin-email admin@acme.example \\
        --admin-password '...'

Add an admin to an existing tenant (no new Tenant row)::

    python manage.py create_tenant_and_admin \\
        --add-admin-only \\
        --slug acme \\
        --admin-username acme_admin2 \\
        --admin-email admin2@acme.example \\
        --admin-password '...'
"""

from __future__ import annotations

import getpass
import sys

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils.text import slugify

from dose.management.schema_utils import tenant_schema_disallowed_reason
from dose.models import PassThroughEndpoint, Tenant, UserProfile, UserTenantMembership

User = get_user_model()

ROLE_MAP = {
    "owner": UserTenantMembership.Role.OWNER,
    "admin": UserTenantMembership.Role.ADMIN,
    "member": UserTenantMembership.Role.MEMBER,
    "viewer": UserTenantMembership.Role.VIEWER,
}


def _seed_passthrough_endpoints(stdout, tenant_obj: Tenant) -> None:
    """Copy passthrough rows from a donor schema into the tenant schema (same idea as bootstrap_auth)."""
    target_schema = (tenant_obj.schema_name or "").strip()
    if not target_schema or target_schema.lower() == "public":
        return

    fields_to_copy = [
        f.name
        for f in PassThroughEndpoint._meta.fields
        if f.name not in {"id", "created_at"}
    ]

    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{target_schema}",public;')
    target_count = PassThroughEndpoint.objects.count()
    if target_count > 0:
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public,pg_catalog")
        stdout.write(
            f"Passthrough endpoints already present in {target_schema} ({target_count}); skip seed."
        )
        return

    source_rows = []
    source_schema = None
    candidate_schemas = ["public"]
    candidate_schemas += list(
        Tenant.objects.exclude(schema_name__in=["public", target_schema]).values_list(
            "schema_name", flat=True
        )
    )

    for schema in candidate_schemas:
        if not schema:
            continue
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema}",public;')
        rows = list(PassThroughEndpoint.objects.all().values(*fields_to_copy))
        if rows:
            source_rows = rows
            source_schema = schema
            break

    if source_rows:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{target_schema}",public;')
        for row in source_rows:
            PassThroughEndpoint.objects.create(**row)
        stdout.write(
            f"Seeded {len(source_rows)} passthrough endpoints from {source_schema} -> {target_schema}"
        )
    else:
        stdout.write(f"No donor passthrough rows found; left {target_schema} empty.")

    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO public,pg_catalog")


class Command(BaseCommand):
    help = (
        "Create a tenant (schema + public.dose_tenant row) and a tenant admin "
        "(User + UserProfile + UserTenantMembership). Optionally run migrate_all_schemas."
    )

    def add_arguments(self, parser):
        parser.add_argument("--tenant-name", type=str, help="Display name for the tenant.")
        parser.add_argument(
            "--slug",
            type=str,
            help="URL slug; schema_name is derived from slug (hyphens -> underscores).",
        )
        parser.add_argument("--admin-username", type=str, required=True, help="Django username.")
        parser.add_argument(
            "--admin-email",
            type=str,
            default="",
            help="Email for the admin user (default: <username>@<slug>.local).",
        )
        parser.add_argument(
            "--admin-password",
            type=str,
            default=None,
            help="Password (omit to be prompted on a TTY; unsafe for logs).",
        )
        parser.add_argument(
            "--role",
            type=str,
            choices=list(ROLE_MAP.keys()),
            default="admin",
            help="UserTenantMembership role (default: admin).",
        )
        parser.add_argument(
            "--superuser",
            action="store_true",
            help="Also set is_superuser (platform-wide). Default: staff-only tenant admin.",
        )
        parser.add_argument(
            "--add-admin-only",
            action="store_true",
            help="Do not create a tenant; attach admin to existing tenant matching --slug.",
        )
        parser.add_argument(
            "--no-migrate",
            action="store_true",
            help="After creating a new tenant, skip migrate_all_schemas (you must run it yourself).",
        )
        parser.add_argument(
            "--no-passthrough-seed",
            action="store_true",
            help="Do not copy passthrough template rows into the new tenant schema.",
        )
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="If the user already exists, set password to --admin-password / prompted value.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print actions only; no database writes.",
        )

    def handle(self, *args, **options):
        add_admin_only = options["add_admin_only"]
        slug = (options.get("slug") or "").strip()
        tenant_name = (options.get("tenant_name") or "").strip()

        if add_admin_only:
            if not slug:
                raise CommandError("--slug is required with --add-admin-only.")
        else:
            if not tenant_name:
                raise CommandError("--tenant-name is required when creating a tenant.")
            if not slug:
                slug = slugify(tenant_name) or None
            if not slug:
                raise CommandError("Could not derive --slug from tenant name; pass --slug explicitly.")

        schema_probe = slug.replace("-", "_").lower()
        bad = tenant_schema_disallowed_reason(schema_probe)
        if bad:
            raise CommandError(f"Invalid slug/schema: {bad}")

        admin_username = options["admin_username"].strip()
        if not admin_username:
            raise CommandError("--admin-username is required.")

        password = options["admin_password"]
        if not password:
            if sys.stdin.isatty():
                p1 = getpass.getpass("Admin password: ")
                p2 = getpass.getpass("Admin password (again): ")
                if p1 != p2:
                    raise CommandError("Passwords do not match.")
                password = p1
            else:
                raise CommandError(
                    "Non-interactive mode: pass --admin-password or set stdin to a TTY."
                )
        if not password:
            raise CommandError("Password is empty.")

        admin_email = (options["admin_email"] or "").strip()
        if not admin_email:
            safe = slugify(slug).replace("-", "") or "tenant"
            admin_email = f"{admin_username}@{safe}.local"

        role = ROLE_MAP[options["role"]]
        dry = options["dry_run"]

        existing = Tenant.objects.filter(slug=slug).first()
        if add_admin_only:
            if existing is None:
                raise CommandError(f"No tenant with slug={slug!r}.")
            tenant = existing
            created_tenant = False
        else:
            if existing is not None:
                raise CommandError(
                    f"Tenant slug={slug!r} already exists (id={existing.id}). "
                    "Use --add-admin-only to add another admin to that tenant."
                )
            created_tenant = True
            if dry:
                self.stdout.write(self.style.WARNING(f"[dry-run] Would create tenant slug={slug!r}"))
                tenant = None
            else:
                tenant = Tenant(name=tenant_name, slug=slug, is_active=True)
                tenant.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Tenant created: id={tenant.id} name={tenant.name!r} schema={tenant.schema_name!r}"
                    )
                )

        if dry:
            self.stdout.write(
                self.style.WARNING(
                    f"[dry-run] Would ensure user={admin_username!r} email={admin_email!r} "
                    f"role={options['role']} superuser={options['superuser']} on tenant slug={slug!r}"
                )
            )
            if created_tenant and not options["no_migrate"]:
                self.stdout.write(self.style.WARNING("[dry-run] Would run migrate_all_schemas"))
            if created_tenant and not options["no_passthrough_seed"]:
                self.stdout.write(self.style.WARNING("[dry-run] Would seed passthrough endpoints"))
            return

        if created_tenant and not dry and tenant is not None and not options["no_migrate"]:
            self.stdout.write(self.style.WARNING("Running migrate_all_schemas (all schemas)..."))
            call_command("migrate_all_schemas", no_input=True, verbosity=1)

        if tenant is None:
            raise CommandError("Internal error: tenant is None after creation.")

        if created_tenant and not options["no_passthrough_seed"]:
            _seed_passthrough_endpoints(self.stdout, tenant)

        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public, pg_catalog")

        with transaction.atomic():
            user, u_created = User.objects.get_or_create(
                username=admin_username,
                defaults={"email": admin_email},
            )
            if admin_email:
                user.email = admin_email
            user.is_active = True
            user.is_staff = True
            user.is_superuser = bool(options["superuser"])
            if u_created or options["reset_password"]:
                user.set_password(password)
            elif not user.has_usable_password():
                user.set_password(password)
            user.save()

            membership, m_created = UserTenantMembership.objects.get_or_create(
                user=user,
                tenant=tenant,
                defaults={"role": role},
            )
            if membership.role != role:
                membership.role = role
                membership.save(update_fields=["role", "updated_at"])

            profile, p_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={"tenant": tenant},
            )
            if profile.tenant_id != tenant.id:
                other = profile.tenant
                raise CommandError(
                    f"User {admin_username!r} already has UserProfile for tenant id={other.id} "
                    f"({other.slug!r}). Use a different --admin-username or remove that profile first."
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: user={admin_username!r} tenant={tenant.slug!r} schema={tenant.schema_name!r} "
                f"membership_role={options['role']} created_user={u_created}"
            )
        )
