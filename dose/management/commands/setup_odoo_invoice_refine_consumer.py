"""Seed Type 3 Odoo invoice narration refine (enqueue + consumer)."""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dose.models import Instruction, Tenant
from dose.tenant_app_lookup import tenant_schema_search_path
from dose.webhook_events import (
    ODOO_INVOICE_REFINE_ACTION_PATH,
    ODOO_INVOICE_REFINE_EVENT_KEY,
)


# Odoo often puts action_post only in the JSON body; URL is plain call_button.
# Also seed URL-contains action_post for builds that bake the method into the path.
_ENQUEUE_PATHS = (
    "/web/dataset/call_button",
    "action_post",
    "/web/dataset/call_kw",
)


class Command(BaseCommand):
    help = (
        "Create/update Odoo invoice Post enqueue + RefineOdooInvoiceDescription "
        "mailbox consumer (Type 3 mid-stream refine)."
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

            for path in _ENQUEUE_PATHS:
                for direction in ("RES", "REQ"):
                    enqueue, created_e = Instruction.objects.update_or_create(
                        tenant=tenant,
                        requestpath=path,
                        requestmethod="POST",
                        direction=direction,
                        defaults={
                            "match_type": "contains",
                            "eventKey": "odoo.invoice.action_post.enqueue",
                            "executescript": "EnqueueOdooInvoiceRefine",
                            "description": (
                                "Type 3: on invoice Post — enqueue Note refine "
                                f"(path contains {path!r}, {direction}; "
                                "atomic filters account.move + action_post)"
                            ),
                            "save_callbackdata": True,
                        },
                    )
                    verb = "Created" if created_e else "Updated"
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{verb} Enqueue #{enqueue.pk}: POST {direction} contains {path!r}"
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
                        "Type 3: RefineOdooInvoiceDescription — AI clean "
                        "account.move.narration + note lines"
                    ),
                    "save_callbackdata": True,
                },
            )
            verb_r = "Created" if created_r else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{verb_r} RefineOdooInvoiceDescription instruction #{refine.pk}: "
                    f"{ODOO_INVOICE_REFINE_ACTION_PATH}"
                )
            )

        self.stdout.write(
            self.style.WARNING(
                "Mailbox consumer must be running. After seed: hard-refresh passthrough, "
                "Reset to Draft → Confirm again (or new invoice) to fire Type 3."
            )
        )
