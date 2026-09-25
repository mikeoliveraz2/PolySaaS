"""
Vendor capture → Captured Topics mailbox enroll (Vendors family).

Same WebhookMailbox / polysaas.capture.v1 stack as Contacts / Inventory / SNMP.
Topic key is RES.vendors.<actor> so Captured Topics lists a Vendors row.
Publish-only: no Instruction that creates records in other apps.
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Type 4 New Vendor Assist — 2026-09-25
from __future__ import annotations

import logging
import uuid

from django.utils import timezone as dj_timezone

logger = logging.getLogger(__name__)

VENDOR_EVENT_KEY = "polysaas.vendor.created"
VENDOR_ACTION_PATH = "/events/polysaas/vendor/created"
VENDOR_CAPTURE_KIND = "polysaas.capture.v1"


def vendor_topic(actor: str = "system") -> str:
    user = (actor or "system").strip().lower().replace(" ", ".") or "system"
    return f"RES.vendors.{user}"


def enroll_vendor_capture(
    *,
    tenant,
    record: dict,
    actor: str = "system",
    action_path: str = VENDOR_ACTION_PATH,
    event_key: str = VENDOR_EVENT_KEY,
    method: str = "POST",
    event_id: str = "",
) -> dict:
    """Enroll one vendor record into WebhookMailbox (pending). Dedup on event_id."""
    from django.db import IntegrityError

    from dose.models import WebhookMailbox
    from dose.models.webhook_mailbox import CAPTURE_MAILBOX_TTL_SECONDS
    from dose.tenant_app_lookup import tenant_schema_search_path

    if tenant is None or not getattr(tenant, "schema_name", None):
        return {"success": False, "error": "no_tenant"}

    rec = record if isinstance(record, dict) else {}
    topic = vendor_topic(actor)
    action_path = action_path or VENDOR_ACTION_PATH
    event_key = event_key or VENDOR_EVENT_KEY
    event_id = (event_id or "").strip() or uuid.uuid4().hex
    correlation_id = str(uuid.uuid4())
    payload = {
        "capture": "vendor_created",
        "topic": topic,
        "records": [rec],
        "record_count": 1,
        "data": rec,
        "odoo_vendor_id": rec.get("odoo_vendor_id"),
        "odoo_contact_id": rec.get("odoo_contact_id"),
        "vendor_name": rec.get("name") or rec.get("vendor_name") or "",
        "email": rec.get("email") or "",
        "region": rec.get("region") or "",
        "criteria": rec.get("criteria") or {},
    }
    envelope = {
        "kind": VENDOR_CAPTURE_KIND,
        "event_id": event_id,
        "correlation_id": correlation_id,
        "tenant_schema": tenant.schema_name,
        "source": "odoo",
        "action_path": action_path,
        "method": method,
        "direction": "RES",
        "event_key": event_key,
        "topic": topic,
        "actor": {"username": actor or "system"},
        "payload": payload,
        "received_at": dj_timezone.now().isoformat(),
    }
    result_summary = {
        "topic": topic,
        "capture": "vendor_created",
        "records": [rec],
        "record_count": 1,
        "data": rec,
    }

    try:
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                return {"success": False, "error": "invalid tenant schema"}
            existing = WebhookMailbox.objects.filter(event_id=event_id).first()
            if existing is not None:
                return {
                    "success": True,
                    "deduped": True,
                    "mailbox_id": existing.id,
                    "event_id": event_id,
                    "topic": topic,
                    "event_key": event_key,
                    "record_count": 1,
                    "expires_at": existing.expires_at.isoformat()
                    if existing.expires_at
                    else None,
                }
            row = WebhookMailbox.create_from_envelope(
                envelope,
                ttl_seconds=CAPTURE_MAILBOX_TTL_SECONDS,
                status="pending",
                result=result_summary,
                tenant=tenant,
            )
        return {
            "success": True,
            "deduped": False,
            "mailbox_id": row.id,
            "event_id": event_id,
            "topic": topic,
            "event_key": event_key,
            "record_count": 1,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        }
    except IntegrityError:
        logger.info("[VendorCapture] enroll deduped event_id=%s", event_id)
        return {
            "success": True,
            "deduped": True,
            "event_id": event_id,
            "topic": topic,
            "event_key": event_key,
            "record_count": 1,
        }
    except Exception as exc:
        logger.warning("[VendorCapture] enroll failed: %s", exc, exc_info=True)
        return {"success": False, "error": str(exc), "event_id": event_id, "event_key": event_key}
