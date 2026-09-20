"""
Diagnose / seed WebhookMailbox for a tenant schema.

  python manage.py diagnose_webhook_mailbox --schema polysaas
  python manage.py diagnose_webhook_mailbox --schema polysaas --seed
  python manage.py diagnose_webhook_mailbox --schema polysaas --dump
"""
from __future__ import annotations

import json
import uuid

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from dose.models import Tenant
from dose.models.webhook_mailbox import CAPTURE_MAILBOX_TTL_SECONDS, WebhookMailbox
from dose.tenant_app_lookup import tenant_schema_search_path


SAMPLE_INVENTORY_RECORDS = (
    {"id": 1, "default_code": "PS-INV-01", "display_name": "Pine 2x4 stud (bundle)", "qty_available": 120.0},
    {"id": 2, "default_code": "PS-INV-02", "display_name": "Plywood 4x8 sheet", "qty_available": 85.0},
    {"id": 3, "default_code": "PS-INV-03", "display_name": "Deck screw box (500)", "qty_available": 200.0},
)


class Command(BaseCommand):
    help = "Count WebhookMailbox rows; --seed writes sample inventory records; --dump shows payload shape."

    def add_arguments(self, parser):
        parser.add_argument("--schema", default="polysaas", help="Tenant schema_name")
        parser.add_argument(
            "--seed",
            action="store_true",
            help="Insert one processed row with sample inventory records[]",
        )
        parser.add_argument(
            "--dump",
            action="store_true",
            help="Print payload keys / record_count for latest rows",
        )

    def handle(self, *args, **options):
        schema = (options["schema"] or "polysaas").strip()
        seed = bool(options["seed"])
        dump = bool(options["dump"])

        with connection.cursor() as cur:
            cur.execute("SET search_path TO public")
        tenant = Tenant.objects.filter(schema_name=schema).first()
        if not tenant:
            self.stderr.write(self.style.ERROR(f"No Tenant with schema_name={schema!r}"))
            return

        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = %s AND table_name = 'webhook_mailbox'
                ORDER BY ordinal_position
                """,
                [schema],
            )
            cols = [r[0] for r in cur.fetchall()]
        self.stdout.write(f"schema={schema} tenant={tenant.name} slug={tenant.slug}")
        self.stdout.write(f"  webhook_mailbox columns: {cols or '(TABLE MISSING)'}")

        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                self.stderr.write(self.style.ERROR("search_path failed"))
                return
            count = WebhookMailbox.objects.count()
            self.stdout.write(f"  row count: {count}")
            for row in WebhookMailbox.objects.all()[:10]:
                payload = (row.envelope or {}).get("payload") if isinstance(row.envelope, dict) else None
                recs = None
                if isinstance(payload, dict):
                    recs = payload.get("records")
                    if recs is None and isinstance(payload.get("data"), dict):
                        recs = payload["data"].get("records")
                n = len(recs) if isinstance(recs, list) else None
                self.stdout.write(
                    f"    #{row.id} status={row.status} source={row.source} "
                    f"topic={row.topic!r} records={n} path={row.action_path!r}"
                )
                if dump:
                    if isinstance(payload, dict):
                        self.stdout.write(f"      payload.keys={list(payload.keys())}")
                        data = payload.get("data")
                        if isinstance(data, dict):
                            self.stdout.write(f"      data.keys={list(data.keys())}")
                            if "records" in data and isinstance(data["records"], list) and data["records"]:
                                self.stdout.write(
                                    f"      data.records[0].keys={list(data['records'][0].keys())}"
                                )
                        if isinstance(recs, list) and recs:
                            self.stdout.write(
                                f"      records[0]={json.dumps(recs[0], default=str)[:300]}"
                            )
                    else:
                        self.stdout.write(f"      payload type={type(payload).__name__}")

            if seed:
                if "topic" not in cols:
                    self.stderr.write(self.style.ERROR(
                        "column topic missing — run: python manage.py migrate"
                    ))
                    return
                records = list(SAMPLE_INVENTORY_RECORDS)
                envelope = {
                    "kind": "polysaas.capture.v1",
                    "event_id": uuid.uuid4().hex,
                    "correlation_id": str(uuid.uuid4()),
                    "tenant_schema": schema,
                    "source": "passthrough",
                    "action_path": "product.product/web_search_read",
                    "method": "POST",
                    "direction": "RES",
                    "event_key": "diagnose_seed_records",
                    "topic": "RES.product.product.web_search_read.diagnose",
                    "payload": {
                        "capture": "post_response",
                        "topic": "RES.product.product.web_search_read.diagnose",
                        "data": {
                            "records": records,
                            "length": len(records),
                            "record_count": len(records),
                            "source": "diagnose_seed",
                        },
                        "records": records,
                        "record_count": len(records),
                    },
                    "received_at": timezone.now().isoformat(),
                }
                row = WebhookMailbox.create_from_envelope(
                    envelope,
                    ttl_seconds=CAPTURE_MAILBOX_TTL_SECONDS,
                    status="processed",
                    result={
                        "seed": True,
                        "records": records,
                        "record_count": len(records),
                    },
                    tenant=tenant,
                )
                self.stdout.write(self.style.SUCCESS(
                    f"  SEED OK id={row.id} records={len(records)} — "
                    "open Admin → Webhook mailboxes → this row → Published records"
                ))
