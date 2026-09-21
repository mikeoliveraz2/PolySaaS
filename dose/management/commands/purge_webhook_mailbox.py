"""
Purge WebhookMailbox rows in a tenant schema (ops workaround if admin delete fails).

  python manage.py purge_webhook_mailbox --schema polysaas --all
  python manage.py purge_webhook_mailbox --schema polysaas --id 6
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection

from dose.models import Tenant
from dose.models.webhook_mailbox import WebhookMailbox
from dose.tenant_app_lookup import tenant_schema_search_path


class Command(BaseCommand):
    help = "Delete WebhookMailbox rows in a tenant schema (schema-qualified)."

    def add_arguments(self, parser):
        parser.add_argument("--schema", default="polysaas")
        parser.add_argument("--id", type=int, action="append", dest="ids", default=[])
        parser.add_argument(
            "--all",
            action="store_true",
            help="Delete every mailbox row in this schema",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List targets only",
        )

    def handle(self, *args, **options):
        schema = (options["schema"] or "polysaas").strip()
        ids = options["ids"] or []
        delete_all = bool(options["all"])
        dry = bool(options["dry_run"])

        with connection.cursor() as cur:
            cur.execute("SET search_path TO public")
        tenant = Tenant.objects.filter(schema_name=schema).first()
        if not tenant:
            self.stderr.write(self.style.ERROR(f"No Tenant schema_name={schema!r}"))
            return
        if not delete_all and not ids:
            self.stderr.write(self.style.ERROR("Pass --all or one/more --id N"))
            return

        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                self.stderr.write(self.style.ERROR("search_path failed"))
                return
            qs = WebhookMailbox.objects.all()
            if ids:
                qs = qs.filter(pk__in=ids)
            rows = list(qs.values_list("id", "topic", "action_path")[:500])
            self.stdout.write(f"schema={schema} matching={qs.count()}")
            for rid, topic, path in rows[:20]:
                self.stdout.write(f"  #{rid} topic={topic!r} path={path!r}")
            if dry:
                self.stdout.write(self.style.WARNING("DRY RUN — no deletes"))
                return
            # Schema-qualified hard delete
            table = WebhookMailbox._meta.db_table
            pks = list(qs.values_list("pk", flat=True))
            if not pks:
                self.stdout.write("Nothing to delete")
                return
            placeholders = ", ".join(["%s"] * len(pks))
            with connection.cursor() as cur:
                cur.execute(
                    f'DELETE FROM "{schema}"."{table}" WHERE id IN ({placeholders})',
                    pks,
                )
            self.stdout.write(self.style.SUCCESS(f"Deleted {len(pks)} row(s)"))
