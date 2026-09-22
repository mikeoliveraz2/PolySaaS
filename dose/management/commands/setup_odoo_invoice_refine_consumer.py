"""Seed Type 3: one passthrough Instruction plus the mailbox transport row.

Both rows call RefineOdooInvoiceDescription. The passthrough row matches the
invoice Confirm POST. The mailbox row is how that same atomic runs after Odoo
has accepted the post, without holding the HTTP response.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dose.models import Instruction, Tenant
from dose.tenant_app_lookup import tenant_schema_search_path
from dose.webhook_events import (
    ODOO_INVOICE_REFINE_ACTION_PATH,
    ODOO_INVOICE_REFINE_EVENT_KEY,
)

# Captured Odoo Confirm URL. action_post lives in the JSON body, not the path.
_CONFIRM_PATH = "/web/dataset/call_button"


def _default_odoo_rpc_params() -> dict:
    """Seed the mailbox refine row with the platform Odoo settings."""
    from django.conf import settings

    return {
        "odoo_url": str(getattr(settings, "ODOO_SHARED_URL", "") or "").rstrip("/"),
        "odoo_db": str(getattr(settings, "ODOO_SHARED_DB", "odoo") or "odoo"),
        "odoo_login": str(getattr(settings, "ODOO_XMLRPC_ADMIN_LOGIN", "admin") or "admin"),
        "odoo_password": str(getattr(settings, "ODOO_XMLRPC_ADMIN_PASSWORD", "") or ""),
    }


class Command(BaseCommand):
    help = (
        "Create/update the Type 3 invoice Confirm instruction. "
        "One atomic: RefineOdooInvoiceDescription."
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

            removed, _ = Instruction.objects.filter(
                executescript="EnqueueOdooInvoiceRefine",
            ).delete()
            if removed:
                self.stdout.write(
                    self.style.WARNING(
                        f"Removed {removed} EnqueueOdooInvoiceRefine instruction(s)"
                    )
                )

            confirm, created_c = Instruction.objects.update_or_create(
                tenant=tenant,
                requestpath=_CONFIRM_PATH,
                requestmethod="POST",
                direction="RES",
                defaults={
                    "match_type": "contains",
                    "eventKey": "odoo.invoice.action_post",
                    "executescript": "RefineOdooInvoiceDescription",
                    "description": (
                        "Type 3: invoice Confirm POST — queue Note refine "
                        "(atomic filters account.move + action_post; POST is not rewritten)"
                    ),
                    "save_callbackdata": True,
                    "parameters_json": _default_odoo_rpc_params(),
                },
            )
            verb_c = "Created" if created_c else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{verb_c} RefineOdooInvoiceDescription instruction #{confirm.pk}: "
                    f"POST RES contains {_CONFIRM_PATH!r}"
                )
            )

            refine, created_r = Instruction.objects.update_or_create(
                tenant=tenant,
                requestpath=ODOO_INVOICE_REFINE_ACTION_PATH,
                requestmethod="POST",
                direction="REQ",
                defaults={
                    "match_type": "path",
                    "eventKey": ODOO_INVOICE_REFINE_EVENT_KEY,
                    "executescript": "RefineOdooInvoiceDescription",
                    "description": (
                        "Type 3 mailbox transport: RefineOdooInvoiceDescription "
                        "cleans account.move.narration after Confirm"
                    ),
                    "save_callbackdata": True,
                    "parameters_json": _default_odoo_rpc_params(),
                },
            )
            verb_r = "Created" if created_r else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{verb_r} mailbox transport instruction #{refine.pk}: "
                    f"{ODOO_INVOICE_REFINE_ACTION_PATH}"
                )
            )

        self.stdout.write(
            self.style.WARNING(
                "Mailbox consumer must be running. Confirm a draft invoice through "
                "passthrough; the green bar reports the Note refine after Odoo posts."
            )
        )
