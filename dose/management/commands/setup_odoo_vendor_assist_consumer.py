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
                        "New Vendor Assist — branded replacement page "
                        "(GET: atomic returns HTML)"
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

            post_instr, post_created = Instruction.objects.update_or_create(
                tenant=tenant,
                requestpath=_VENDOR_NEW_PATH,
                requestmethod="POST",
                direction="REQ",
                defaults={
                    "match_type": "path",
                    "eventKey": "odoo.vendor.new.assist.criteria",
                    "executescript": _ATOMIC,
                    "description": (
                        "Slice 2–3: New Vendor Assist — capture criteria then "
                        "return a demo-directory shortlist (POST JSON; DoseMessage toasts)"
                    ),
                    "save_callbackdata": True,
                    "parameters_json": {
                        "capture_criteria": True,
                        "suggest_vendors": True,
                    },
                },
            )
            post_verb = "Created" if post_created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{post_verb} {_ATOMIC} instruction #{post_instr.pk} in schema "
                    f"{schema!r}: POST REQ path {_VENDOR_NEW_PATH!r} "
                    f"(eventKey=odoo.vendor.new.assist.criteria)"
                )
            )


        self.stdout.write(
            self.style.WARNING(
                "Hard-refresh Odoo passthrough, open Vendors -> New. "
                "Expect Assist page, 'Vendor page loaded', then Find suppliers "
                "toasts 'Criteria captured' then 'Shortlist returned'."
            )
        )
