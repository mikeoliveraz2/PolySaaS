"""
Seed SNMP → Odoo Maintenance Instruction for Type 2 + Type 1 demo.

Usage:
    python manage.py seed_snmp_odoo_maintenance             # default: polysaas
    python manage.py seed_snmp_odoo_maintenance olient
    python manage.py seed_snmp_odoo_maintenance --dry-run
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Seed SnmpToOdooMaintenance Instruction for a tenant."

    def add_arguments(self, parser):
        parser.add_argument(
            "tenant_slug",
            nargs="?",
            default="polysaas",
            help="Tenant slug (default: polysaas)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be created without writing to DB",
        )
        parser.add_argument(
            "--delete-existing",
            action="store_true",
            help="Delete existing snmp.telemetry Instructions before re-seeding",
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

        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{tenant.schema_name}", public')

        event_key = "snmp.telemetry"
        spec = {
            "event_key": event_key,
            "match_type": "contains",
            "match_value": "/webhook/snmp/",
            "direction": "REQ",
            "method_filter": "POST",
            "description": "SNMP telemetry inbound → mailbox + Odoo Maintenance",
            "executescript": "SnmpToOdooMaintenance",
            "save_callbackdata": True,
            "parameters_json": {
                "temp_critical_c": 60,
                "create_requests": True,
            },
        }

        if dry_run:
            self.stdout.write(f"  [DRY-RUN] Would upsert Instruction: {event_key}")
            self.stdout.write(f"  executescript={spec['executescript']}")
            self.stdout.write(f"  parameters_json={spec['parameters_json']}")
            return

        if delete_existing:
            deleted, _ = Instruction.objects.filter(
                tenant=tenant,
                eventKey=event_key,
            ).delete()
            if deleted:
                self.stdout.write(f"  Deleted {deleted} existing instruction(s) for {event_key}")

        instruction, created = Instruction.objects.update_or_create(
            tenant=tenant,
            eventKey=event_key,
            defaults={
                "match_type": spec["match_type"],
                "requestpath": spec["match_value"],
                "direction": spec["direction"],
                "requestmethod": spec["method_filter"],
                "description": spec["description"],
                "executescript": spec["executescript"],
                "save_callbackdata": spec["save_callbackdata"],
                "parameters_json": spec["parameters_json"],
            },
        )

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"  {action} Instruction: {event_key} (pk={instruction.pk})"
            )
        )
        self.stdout.write(
            f"\nPOST feed URL:\n"
            f"  /dose/webhook/snmp/{slug}/\n"
            f"Run: python scripts/snmp_week_feed.py --week 1 --tenant {slug}\n"
            f"Then: python scripts/snmp_week_feed.py --week 2 --tenant {slug}"
        )
