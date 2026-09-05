"""Tenant-safe DoseMessage helpers.

DoseMessage rows live in the tenant schema. Auth users live in public. The
ORM FK stays so unread filters still work; the database constraint is off so a
public user id does not have to exist in tenant auth_user.
"""
from __future__ import annotations

import logging

from dose.tenant_app_lookup import tenant_schema_search_path

logger = logging.getLogger(__name__)


def create_dose_message(*, tenant, user=None, message: str, level: str = "info"):
    """Create one DoseMessage in the tenant schema. Never raises to callers."""
    if not tenant or not (message or "").strip():
        return None
    try:
        from dose.models import DoseMessage

        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                return None
            auth_user = None
            if user is not None and getattr(user, "is_authenticated", False):
                auth_user = user
            return DoseMessage.objects.create(
                user=auth_user,
                message=message.strip(),
                level=level if level in ("info", "success", "warning", "error") else "info",
            )
    except Exception:
        logger.exception("create_dose_message failed tenant=%s", getattr(tenant, "schema_name", "?"))
        return None


def feedback_text_for_result(instruction, result: dict, service_name: str) -> tuple[str, str]:
    """Return (message, level) for an orchestration atomic result."""
    level = "success"
    if isinstance(result, dict) and result.get("status") in ("error", "failed"):
        level = "error"
        detail = result.get("detail") or result.get("error") or "unknown error"
        return f"Consumer failed: {detail}", level

    if isinstance(result, dict):
        if result.get("partner_id"):
            return f"Odoo contact ready — partner #{result['partner_id']}", level
        if result.get("order_name") or result.get("order_id"):
            name = result.get("order_name") or f"#{result.get('order_id')}"
            return f"Odoo draft quotation {name}", level

    event_key = getattr(instruction, "eventKey", "") or ""
    name = getattr(instruction, "executescript", None) or service_name or "OrchestratedEvent"
    if event_key:
        return f"Orchestration: {name} executed ({event_key})", "info"
    return f"Orchestration: {name} executed", "info"


def create_orchestration_feedback(*, tenant, user, instruction, result: dict) -> object | None:
    text, level = feedback_text_for_result(
        instruction,
        result if isinstance(result, dict) else {},
        getattr(instruction, "executescript", None) or "OrchestratedEvent",
    )
    return create_dose_message(tenant=tenant, user=user, message=text, level=level)


def list_recent_messages(*, tenant, user=None, limit: int = 40) -> list[dict]:
    """Newest-first DoseMessages for the wireframe thread."""
    from dose.models import DoseMessage

    with tenant_schema_search_path(tenant) as ok:
        if not ok:
            return []
        from django.db.models import Q

        qs = DoseMessage.objects.order_by("-created_at", "-id")
        if user is not None and getattr(user, "is_authenticated", False):
            # Filter by PK only — avoid joining tenant auth_user for public users.
            qs = qs.filter(Q(user_id=user.pk) | Q(user_id__isnull=True))
        rows = list(qs[: max(1, min(limit, 100))])
        out = []
        for row in reversed(rows):
            out.append(
                {
                    "id": row.id,
                    "message": row.message,
                    "level": row.level,
                    "is_read": row.is_read,
                    "created_at": row.created_at.isoformat() if row.created_at else "",
                    # Do not join auth_user in the tenant schema — user_id is a
                    # public User PK. Author label is resolved at write time or
                    # shown generically here.
                    "author": "PolySaaS" if row.user_id is None else "you",
                }
            )
        return out
