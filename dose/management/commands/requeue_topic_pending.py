"""
Re-queue processed mailbox rows for a topic so Topic browser Consume can drain them.

Usage:
  python manage.py requeue_topic_pending --schema polysaas --topic-contains product.template
  python manage.py requeue_topic_pending --schema polysaas --all-captures
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Set WebhookMailbox rows back to pending for Topic Consume."

    def add_arguments(self, parser):
        parser.add_argument("--schema", default="polysaas")
        parser.add_argument(
            "--topic-contains",
            default="",
            help="Only topics containing this substring",
        )
        parser.add_argument(
            "--all-captures",
            action="store_true",
            help="All source=passthrough or source=snmp processed rows",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        schema = options["schema"]
        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema}", public')

        from dose.models import WebhookMailbox

        qs = WebhookMailbox.objects.filter(status="processed")
        if options["topic_contains"]:
            qs = qs.filter(topic__icontains=options["topic_contains"])
        elif options["all_captures"]:
            qs = qs.filter(source__in=["passthrough", "snmp"])
        else:
            self.stderr.write("Pass --topic-contains or --all-captures")
            return

        count = qs.count()
        self.stdout.write(f"schema={schema} matching processed rows={count}")
        if options["dry_run"] or count == 0:
            return
        updated = qs.update(
            status="pending",
            processed_at=None,
            claimed_at=None,
            error="",
        )
        self.stdout.write(self.style.SUCCESS(f"Re-queued {updated} row(s) to pending"))
