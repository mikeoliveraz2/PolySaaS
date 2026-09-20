"""
Maintain webhook/capture mailboxes: useful TTL → dead_letter → purge.

  python manage.py maintain_webhook_mailboxes
  python manage.py maintain_webhook_mailboxes --schema polysaas
  python manage.py maintain_webhook_mailboxes --purge-days 14 --dry-run
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection

from dose.models import Tenant
from dose.models.webhook_mailbox import DEAD_LETTER_PURGE_AFTER_DAYS, WebhookMailbox
from dose.tenant_app_lookup import tenant_schema_search_path


class Command(BaseCommand):
    help = (
        "Move past-useful mailbox rows to dead_letter, then purge old dead letters. "
        "Runs across all tenant schemas (or one --schema)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--schema",
            default="",
            help="Limit to one tenant schema_name (default: all active tenants)",
        )
        parser.add_argument(
            "--purge-days",
            type=int,
            default=DEAD_LETTER_PURGE_AFTER_DAYS,
            help=f"Hard-delete dead_letter rows older than N days (default {DEAD_LETTER_PURGE_AFTER_DAYS})",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Count only; do not update or delete",
        )

    def handle(self, *args, **options):
        schema = (options["schema"] or "").strip()
        purge_days = int(options["purge_days"])
        dry_run = bool(options["dry_run"])

        with connection.cursor() as cur:
            cur.execute("SET search_path TO public")

        if schema:
            tenants = list(Tenant.objects.filter(schema_name=schema))
        else:
            tenants = list(
                Tenant.objects.filter(is_active=True).exclude(schema_name__iexact="public")
            )

        if not tenants:
            self.stderr.write(self.style.ERROR("No tenants matched"))
            return

        total_dead = 0
        total_purged = 0
        for tenant in tenants:
            with tenant_schema_search_path(tenant) as ok:
                if not ok:
                    self.stderr.write(self.style.WARNING(f"skip {tenant.schema_name}: bad schema"))
                    continue
                if dry_run:
                    from django.utils import timezone
                    now = timezone.now()
                    dead_n = WebhookMailbox.objects.filter(
                        expires_at__lte=now,
                    ).exclude(status="dead_letter").count()
                    from datetime import timedelta
                    cutoff = now - timedelta(days=purge_days)
                    purge_n = WebhookMailbox.objects.filter(
                        status="dead_letter",
                        processed_at__lte=cutoff,
                    ).count()
                    self.stdout.write(
                        f"  {tenant.schema_name}: would dead_letter={dead_n} purge={purge_n}"
                    )
                    total_dead += dead_n
                    total_purged += purge_n
                else:
                    dead_n = WebhookMailbox.expire_old_entries()
                    purge_n = WebhookMailbox.purge_dead_letters(older_than_days=purge_days)
                    self.stdout.write(
                        f"  {tenant.schema_name}: dead_letter={dead_n} purged={purge_n}"
                    )
                    total_dead += dead_n
                    total_purged += purge_n

        label = "would move/purge" if dry_run else "moved/purged"
        self.stdout.write(self.style.SUCCESS(
            f"Done ({label}): dead_letter={total_dead} purged={total_purged}"
        ))
