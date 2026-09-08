# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo Contact Creation — 2026-09-06

"""
Seed Slack message → Odoo contact creation orchestration Instructions.

Creates tenant-scoped Instructions so the orchestration hook fires when a
Slack message with contact format is received, then wires it to the
OdooCreatePartner atomic service.

Usage:
    python manage.py seed_slack_contact_orchestration             # default: olient
    python manage.py seed_slack_contact_orchestration <slug>      # specific tenant
    python manage.py seed_slack_contact_orchestration --dry-run   # preview only
"""
from __future__ import annotations

import json

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Seed Slack → Odoo contact creation Instructions for a tenant."

    def add_arguments(self, parser):
        parser.add_argument(
            "tenant_slug",
            nargs="?",
            default="olient",
            help="Tenant slug (default: olient)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be created without writing to DB",
        )
        parser.add_argument(
            "--delete-existing",
            action="store_true",
            help="Delete existing slack.message.contact Instructions before re-seeding",
        )

    def handle(self, *args, **options):
        slug = options["tenant_slug"]
        dry_run = options["dry_run"]
        delete_existing = options["delete_existing"]

        from dose.models import Instruction, Tenant

        with connection.cursor() as cur:
            cur.execute("SET search_path TO public")

        tenant = Tenant.objects.filter(slug=slug).first()
        if not tenant:
            self.stderr.write(self.style.ERROR(f"Tenant not found: {slug}"))
            return

        self.stdout.write(f"Tenant: {tenant.name} (schema: {tenant.schema_name})")

        # Set search_path to the tenant schema for subsequent ORM operations
        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{tenant.schema_name}", public')

        # ── Instruction to create ────────────────────────────────────────────
        # Slack Events API — message with contact format
        instruction_spec = {
            "event_key": "slack.message.contact",
            "action_path": "/events/slack/message/contact",
            "direction": "REQ",
            "method_filter": "POST",
            "description": "Slack message → Odoo contact creation (format: 'New contact: Name, email, Company')",
            "executescript": "OdooCreatePartner",
            "save_callbackdata": True,
        }

        if dry_run:
            self.stdout.write(
                f"  [DRY-RUN] Would upsert Instruction: {instruction_spec['event_key']}"
            )
            self.stdout.write(f"    Action Path: {instruction_spec['action_path']}")
            self.stdout.write(f"    Atomic Service: {instruction_spec['executescript']}")
            self.stdout.write(self.style.WARNING("Dry run complete — no changes written."))
            return

        if delete_existing:
            deleted, _ = Instruction.objects.filter(
                tenant=tenant,
                eventKey=instruction_spec["event_key"],
            ).delete()
            if deleted:
                self.stdout.write(
                    f"  Deleted {deleted} existing instruction(s) for {instruction_spec['event_key']}"
                )

        instruction, created = Instruction.objects.update_or_create(
            tenant=tenant,
            eventKey=instruction_spec["event_key"],
            defaults={
                "match_type": "exact",
                "requestpath": instruction_spec["action_path"],
                "direction": instruction_spec["direction"],
                "requestmethod": instruction_spec["method_filter"],
                "description": instruction_spec["description"],
                "executescript": instruction_spec["executescript"],
                "save_callbackdata": instruction_spec["save_callbackdata"],
            },
        )

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"  {action} Instruction: {instruction_spec['event_key']} (pk={instruction.pk})"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone: Instruction {'created' if created else 'updated'} for tenant '{slug}'"
            )
        )
        self.stdout.write(
            "\nTo test the orchestration:"
        )
        self.stdout.write(
            "  1. Configure Slack Events API subscription to message.channels"
        )
        self.stdout.write(
            "  2. Set webhook URL to: https://your-domain/hooks/slack/events/"
        )
        self.stdout.write(
            "  3. Post a message in Slack: 'New contact: Jane Doe, jane@acme.com, Acme Corp'"
        )
        self.stdout.write(
            "  4. Check Odoo Contacts to verify the new contact was created"
        )
