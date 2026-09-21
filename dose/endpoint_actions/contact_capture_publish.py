"""Publishers for Capture contacts → Captured Topics mailbox."""
from __future__ import annotations

from types import SimpleNamespace

from dose.endpoint_data.envelope import (
    build_envelope,
    count_detail,
    error_envelope,
)
from dose.passthrough.orchestration_log import ensure_tenant_search_path


def _publish_capture(tenant, payload: dict, *, load_service, vendor_key: str, action_path: str) -> dict:
    if not tenant or not getattr(tenant, "schema_name", None):
        return {
            "success": False,
            "error": "no tenant",
            "envelope": error_envelope("contact", "no tenant", error="no tenant"),
        }
    if not ensure_tenant_search_path(tenant, f"{vendor_key}_capture_contacts"):
        return {
            "success": False,
            "error": "invalid tenant schema",
            "envelope": error_envelope(
                "contact", "invalid tenant schema", error="invalid tenant schema"
            ),
        }

    request = SimpleNamespace(
        tenant=tenant,
        mq_message_data=dict(payload or {}),
        body=b"{}",
        atomic_parameters=[],
        user=None,
    )
    result = load_service().execute_and_save(request, None)
    ok = result.get("status") == "success"
    count = int(result.get("count") or 0)
    rows = result.get("contacts") if isinstance(result.get("contacts"), list) else []

    if ok:
        topic = result.get("topic") or ""
        detail = count_detail("contact", count)
        if topic:
            detail = f"{detail} → Captured Topics ({topic})"
        envelope = build_envelope("contact", status="success", rows=rows, detail=detail)
    else:
        detail = result.get("detail") or result.get("error") or "Could not capture contacts"
        envelope = error_envelope("contact", detail, error=result.get("error") or "error")

    vendor_block = result.get(vendor_key)
    if not isinstance(vendor_block, dict):
        vendor_block = {}

    return {
        "success": ok,
        "sync": True,
        "status": result.get("status"),
        "count": count,
        "detail": detail if ok else (result.get("detail") or result.get("error")),
        "action_path": action_path,
        "list_kind": "contacts",
        "error": None if ok else (result.get("detail") or result.get("error")),
        "topic": result.get("topic"),
        "mailbox_id": result.get("mailbox_id"),
        "mailbox": result.get("mailbox"),
        "matching_event_key": action_path,
        "callback_description": f"{vendor_key.title()} contacts → Captured Topics",
        vendor_key: vendor_block,
        "contacts": rows,
        "envelope": envelope,
        "popup": "callback_record",
    }


def publish_odoo_capture_contacts(tenant, payload: dict) -> dict:
    from dose.services.odoo_capture_contacts import OdooCaptureContacts

    return _publish_capture(
        tenant,
        payload,
        load_service=lambda: OdooCaptureContacts,
        vendor_key="odoo",
        action_path="odoo.capture_contacts",
    )


def publish_mattermost_capture_contacts(tenant, payload: dict) -> dict:
    from dose.services.mattermost_list_contacts import MattermostListContacts

    return _publish_capture(
        tenant,
        payload,
        load_service=lambda: MattermostListContacts,
        vendor_key="mattermost",
        action_path="mattermost.capture_contacts",
    )
