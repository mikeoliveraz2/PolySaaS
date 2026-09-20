"""
Provision CapturePostResponse Instructions for Odoo Inventory list loads.

Odoo Inventory renders from the POST web_search_read response dict
(``result.records``) — that is what we capture into WebhookMailbox.

  python manage.py setup_odoo_inventory_capture --schema polysaas
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection

from dose.models import Instruction, Tenant


# Paths that return inventory product / stock rows before the SPA paints.
INVENTORY_CAPTURE_PATHS = (
    ("product.product/web_search_read", "odoo_inventory_product_product"),
    ("product.template/web_search_read", "odoo_inventory_product_template"),
    ("stock.quant/web_search_read", "odoo_inventory_stock_quant"),
)


class Command(BaseCommand):
    help = (
        "Create RES+POST CapturePostResponse Instructions for Odoo Inventory "
        "web_search_read responses (product rows → mailbox)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--schema",
            default="polysaas",
            help="Tenant schema_name (default: polysaas)",
        )

    def handle(self, *args, **options):
        schema = (options["schema"] or "polysaas").strip()

        with connection.cursor() as cur:
            cur.execute("SET search_path TO public")
        tenant = Tenant.objects.filter(schema_name=schema).first()
        if not tenant:
            self.stderr.write(self.style.ERROR(f"No Tenant schema_name={schema!r}"))
            return

        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema}", public')

        created = updated = 0
        for requestpath, event_key in INVENTORY_CAPTURE_PATHS:
            obj, was_created = Instruction.objects.update_or_create(
                tenant=tenant,
                requestpath=requestpath,
                direction="RES",
                requestmethod="POST",
                defaults={
                    "match_type": "contains",
                    "match_extra": {},
                    "executescript": "CapturePostResponse",
                    "eventKey": event_key,
                    "description": (
                        "Capture Odoo Inventory list rows from web_search_read "
                        "response (result.records) into Webhook mailbox."
                    ),
                    "save_callbackdata": False,
                    "appusername": "demo",
                    "urllist": "",
                },
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  created id={obj.pk} path={requestpath!r}"
                ))
            else:
                updated += 1
                self.stdout.write(f"  updated id={obj.pk} path={requestpath!r}")

        self.stdout.write(self.style.SUCCESS(
            f"Done schema={schema}: created={created} updated={updated}. "
            "Open Odoo Inventory (Products / Locations) via passthrough, then "
            "check Admin → Webhook mailboxes for records[]."
        ))
