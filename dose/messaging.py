"""Tenant-safe DoseMessage helpers.

DoseMessage rows live in the tenant schema. Auth users live in public. The
ORM FK stays so unread filters still work; the database constraint is off so a
public user id does not have to exist in tenant auth_user.
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Odoo invoice Note refine — 2026-09-23
# Owner-approved 2026-09-22: Type 3 invoice refine feedback copy.
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


def _short_bar_detail(text: str, limit: int = 180) -> str:
    """One line, capped, safe to show on the green bar."""
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) > limit:
        return cleaned[: limit - 1].rstrip() + "…"
    return cleaned


def _is_invoice_refine(instruction, result: dict, service_name: str) -> bool:
    blob = " ".join(
        [
            str(getattr(instruction, "executescript", "") or ""),
            str(service_name or ""),
            str(result.get("service_name") or ""),
            str(getattr(instruction, "eventKey", "") or ""),
        ]
    ).lower()
    compact = blob.replace(" ", "")
    return (
        "refineodooinvoicedescription" in compact
        or "invoice.refine" in blob
        or "invoice/refine" in blob
    )


def _refine_error_detail(result: dict) -> str:
    detail = str(result.get("detail") or "").strip()
    if detail:
        return _short_bar_detail(detail)
    err = str(result.get("error") or "").strip()
    if err == "auth_failed":
        return "Odoo authentication failed"
    if err and err not in ("error", "failed"):
        return _short_bar_detail(err)
    for outcome in result.get("outcomes") or []:
        if not isinstance(outcome, dict):
            continue
        piece = str(outcome.get("detail") or outcome.get("error") or "").strip()
        if piece:
            return _short_bar_detail(piece)
        for line in outcome.get("line_notes") or []:
            if isinstance(line, dict) and line.get("error"):
                return _short_bar_detail(line.get("error"))
    return ""


def feedback_text_for_result(instruction, result: dict, service_name: str) -> tuple[str, str]:
    """Return (message, level) for an orchestration atomic result."""
    level = "success"
    if isinstance(result, dict) and result.get("status") in ("error", "failed"):
        # Invoice refine failures must say "refine" so the green bar leaves "refining note…".
        # The error text itself is part of the message so the bar can show why.
        if _is_invoice_refine(instruction, result if isinstance(result, dict) else {}, service_name):
            detail = _refine_error_detail(result)
            msg = "Invoice description refine skipped"
            if detail:
                msg += f": {detail}"
            return msg, "warning"
        level = "error"
        detail = result.get("detail") or result.get("error") or "unknown error"
        return f"Consumer failed: {detail}", level

    if isinstance(result, dict):
        # Slack → Odoo contact creation (enhanced narrative)
        event_key = getattr(instruction, "eventKey", "") or ""
        if event_key == "slack.message.contact" and result.get("partner_id"):
            name = result.get("name", "contact")
            email = result.get("email", "")
            partner_id = result.get("partner_id")
            created = result.get("created", False)
            action = "created" if created else "updated"
            msg = f"✓ Slack → Odoo: {action} contact '{name}'"
            if email:
                msg += f" ({email})"
            msg += f" — partner #{partner_id}"
            return msg, level
        
        # Generic partner creation
        if result.get("partner_id"):
            return f"Odoo contact ready — partner #{result['partner_id']}", level
        
        # Quotation creation
        if result.get("order_name") or result.get("order_id"):
            name = result.get("order_name") or f"#{result.get('order_id')}"
            return f"Odoo draft quotation {name}", level

        # Type 3: invoice narration refine
        if result.get("queued") and result.get("move_ids"):
            ids = result.get("move_ids") or []
            return f"Invoice Post — refining note (move {ids[0]})…", "info"
        if result.get("outcomes") is not None or (
            result.get("changed") is not None
            and (result.get("invoice_ref") or result.get("move_ids"))
        ):
            outcomes = result.get("outcomes") or []
            changed = [o for o in outcomes if isinstance(o, dict) and o.get("changed")]
            if changed:
                ref = (
                    result.get("invoice_ref")
                    or changed[0].get("invoice_name")
                    or changed[0].get("move_id")
                    or "invoice"
                )
                return f"Invoice {ref} description refined", level
            if any(
                isinstance(o, dict) and o.get("reason") == "ai_failed_soft" for o in outcomes
            ):
                detail = _refine_error_detail({"outcomes": outcomes})
                msg = "Invoice description refine skipped (AI unavailable)"
                if detail:
                    msg += f": {detail}"
                return msg, "warning"
            if outcomes:
                ref = result.get("invoice_ref") or "invoice"
                return f"Invoice {ref} description — no change", "info"

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
