"""Seed Type 3 Odoo invoice narration refine (enqueue + consumer)."""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dose.models import Instruction, Tenant
from dose.tenant_app_lookup import tenant_schema_search_path
from dose.webhook_events import (
    ODOO_INVOICE_REFINE_ACTION_PATH,
    ODOO_INVOICE_REFINE_EVENT_KEY,
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

            # 1) Passthrough match: call_button → enqueue mailbox (async)
            enqueue, created_e = Instruction.objects.update_or_create(
                tenant=tenant,
                requestpath="/web/dataset/call_button",
                requestmethod="POST",
                direction="RES",
                defaults={
                    "match_type": "contains",
                    "eventKey": "odoo.invoice.action_post.enqueue",
                    "executescript": "EnqueueOdooInvoiceRefine",
                    "description": (
                        "Type 3: on invoice Post (call_button/action_post) "
                        "enqueue narration refine (async mailbox)"
                    ),
                    "save_callbackdata": True,
                },
            )
            verb_e = "Created" if created_e else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{verb_e} EnqueueOdooInvoiceRefine instruction #{enqueue.pk} "
                    f"(contains /web/dataset/call_button RES)"
                )
            )

            # 2) Mailbox consumer: refine narration
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
                        "account.move.narration"
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
                "Confirm live Post path via orch bar if call_button does not match; "
                "adjust enqueue Instruction.requestpath if needed."
            )
        )
