"""Seed Slice 1 New Vendor Assist: Instruction → OdooVendorAssist atomic.

Creates a tenant-schema Instruction matching GET /odoo/vendors/new so
passthrough instruction_page serves the branded Assist page. Never writes
to public.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dose.models import Instruction, Tenant
from dose.tenant_app_lookup import tenant_schema_search_path

_VENDOR_NEW_PATH = "/odoo/vendors/new"
_EVENT_KEY = "odoo.vendor.new.assist"
_ATOMIC = "OdooVendorAssist"


class Command(BaseCommand):
    help = (
        "Create/update the New Vendor Assist instruction "
        "(GET /odoo/vendors/new → OdooVendorAssist)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--schema", required=True)

    def handle(self, *args, **options):
        schema = options["schema"].strip()
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public;")
        tenant = Tenant.objects.filter(
            schema_name=schema,
            is_active=True,
        ).first()
        if not tenant or schema.lower() == "public":
            raise CommandError(f"Active tenant schema not found: {schema}")

        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                raise CommandError(f"Could not select tenant schema: {schema}")

            instr, created = Instruction.objects.update_or_create(
                tenant=tenant,
                requestpath=_VENDOR_NEW_PATH,
                requestmethod="GET",
                direction="REQ",
                defaults={
                    "match_type": "path",
                    "eventKey": _EVENT_KEY,
                    "executescript": _ATOMIC,
                    "description": (
                        "Slice 1: New Vendor Assist — branded replacement page "
                        "(atomic returns HTML; no AI/RPC yet)"
                    ),
                    "save_callbackdata": True,
                    "parameters_json": {"serve_page": True},
                },
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{verb} {_ATOMIC} instruction #{instr.pk} in schema "
                    f"{schema!r}: GET REQ path {_VENDOR_NEW_PATH!r} "
                    f"(eventKey={_EVENT_KEY})"
                )
            )

        self.stdout.write(
            self.style.WARNING(
                "Hard-refresh Odoo passthrough, open Vendors -> New. "
                "Expect Assist page and green-bar 'Vendor page loaded'."
            )
        )
