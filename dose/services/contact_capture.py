"""
Cross-app contact capture → Captured Topics mailbox enroll.

External apps (Odoo, Mattermost, Slack, HubSpot) list contacts via their
APIs; we normalize to a common record shape and enroll a polysaas.capture.v1
envelope on the shared topic RES.contacts.<actor> for Consume → ContactHistory.
Source app is kept on each record (not in the topic key).
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from django.utils import timezone as dj_timezone

logger = logging.getLogger(__name__)

MAX_CONTACT_PAGES = 50
PAGE_SIZE = 200


def normalize_contact(
    *,
    source_app: str,
    external_id: Any = None,
    name: str = "",
    email: str = "",
    phone: str = "",
    company: str = "",
    username: str = "",
    active: bool = True,
    raw_record: dict | None = None,
) -> dict:
    """Common contact record for mailbox payload + ContactHistory."""
    return {
        "source_app": (source_app or "").strip().lower()[:32],
        "external_id": str(external_id) if external_id is not None else "",
        "name": (name or "").strip()[:255],
        "email": (email or "").strip()[:255],
        "phone": (phone or "").strip()[:64],
        "company": (company or "").strip()[:255],
        "username": (username or "").strip()[:128],
        "active": bool(active),
        "raw_record": raw_record if isinstance(raw_record, dict) else {},
    }


def contact_topic(source_app: str = "", actor: str = "system") -> str:
    """Shared contacts topic for every app — source_app is on the record, not the key."""
    user = (actor or "system").strip().lower().replace(" ", ".") or "system"
    return f"RES.contacts.{user}"


def enroll_contact_capture(
    *,
    tenant,
    source_app: str,
    records: list[dict],
    actor: str = "system",
    action_path: str = "",
    event_key: str = "",
    method: str = "GET",
    event_id: str = "",
    payload_extra: dict | None = None,
) -> dict:
    """
    Enroll normalized contact records into WebhookMailbox (pending).

    Returns mailbox enroll summary: success, mailbox_id, topic, record_count.
    Optional event_id is unique per tenant schema (WebhookMailbox.event_id);
    a repeat enroll with the same id is a no-op (deduped).
    """
    from django.db import IntegrityError

    from dose.models import WebhookMailbox
    from dose.models.webhook_mailbox import CAPTURE_MAILBOX_TTL_SECONDS
    from dose.tenant_app_lookup import tenant_schema_search_path

    if tenant is None or not getattr(tenant, "schema_name", None):
        return {"success": False, "error": "no_tenant"}

    app = (source_app or "").strip().lower() or "app"
    topic = contact_topic(app, actor)
    action_path = action_path or f"{app}/contacts"
    event_key = event_key or f"{app}.capture_contacts"

    clean = [r for r in (records or []) if isinstance(r, dict)]
    event_id = (event_id or "").strip() or uuid.uuid4().hex
    correlation_id = str(uuid.uuid4())
    extra = payload_extra if isinstance(payload_extra, dict) else {}
    data = {
        "records": clean,
        "record_count": len(clean),
        "length": len(clean),
        "source": f"{app}_contacts",
        "source_app": app,
    }
    payload = {
        "capture": "contact_list",
        "topic": topic,
        "data": data,
        "records": clean,
        "record_count": len(clean),
    }
    for key, value in extra.items():
        if key not in payload:
            payload[key] = value
    envelope = {
        "kind": "polysaas.capture.v1",
        "event_id": event_id,
        "correlation_id": correlation_id,
        "tenant_schema": tenant.schema_name,
        "source": app,
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
        "capture": "contact_list",
        "source_app": app,
        "records": clean,
        "record_count": len(clean),
        "data": data,
    }
    for key, value in extra.items():
        if key not in result_summary:
            result_summary[key] = value

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
                    "record_count": len(clean),
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
            "record_count": len(clean),
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        }
    except IntegrityError:
        logger.info("[ContactCapture] enroll deduped event_id=%s", event_id)
        return {
            "success": True,
            "deduped": True,
            "event_id": event_id,
            "topic": topic,
            "record_count": len(clean),
        }
    except Exception as exc:
        logger.warning("[ContactCapture] enroll failed: %s", exc, exc_info=True)
        return {"success": False, "error": str(exc)}
