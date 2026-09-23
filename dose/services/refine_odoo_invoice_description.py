"""Refine Odoo invoice Note mid-stream (Type 3).

One atomic, two entries:
  - Live Confirm POST (account.move action_post): publish a mailbox job and
    return immediately. The passthrough already forwarded that POST to Odoo.
  - Mailbox replay: read account.move.narration → AI clean → write back
    with the same Odoo session that posted the invoice.

Guardrails:
  - Tenant schema on every ORM/RPC
  - Idempotent: skip write when cleaned equals current (no refine loop)
  - Fail soft: AI/RPC errors leave Odoo text untouched
  - Field: narration (the invoice Note) plus "Add a note" lines
  - PII: send narration text only to the LLM
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Odoo invoice Note refine — 2026-09-23 — commit ac654503
from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import (
    maybe_save_callback,
    service_result,
    tenant_from_request,
)
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.odoo_rpc import (
    OdooRpcClient,
    OdooRpcError,
    load_odoo_rpc_config,
    public_config,
)

logger = logging.getLogger(__name__)

REFINE_SYSTEM_PROMPT = (
    "You clean invoice description / narration text for a business ERP.\n"
    "Rules:\n"
    "- Fix spelling and grammar.\n"
    "- Remove foul or unprofessional language; use a professional business tone.\n"
    "- Keep amounts, numbers, dates, currencies, and SKUs unchanged.\n"
    "- Preserve the language of the original text.\n"
    "- Return plain text only — no quotes, no markdown, no preamble.\n"
    "- If the text is already clean, return it unchanged.\n"
)

_MIN_LEN = 3


class RefineOdooInvoiceDescription(AtomicServiceBase):
    atomic_apps = ("odoo",)
    atomic_category = "write"

    @staticmethod
    def get_parameters(parameters, key="RefineOdooInvoiceDescription"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        # Mailbox replay already carries move ids. Do that before the Confirm
        # gate so writing the Note back cannot queue another refine.
        if _is_mailbox_replay(request):
            return _refine_moves(request, instruction_row)

        body = _request_json(request)
        path = getattr(request, "path", "") or ""
        if _is_invoice_action_post(body, path):
            return _queue_confirm(request, instruction_row, body)

        return service_result(
            "RefineOdooInvoiceDescription",
            status="skipped",
            reason="not_account_move_action_post",
        )


def _refine_moves(request, instruction_row):
    payload = _extract_payload(request, instruction_row)
    move_ids = _coerce_move_ids(payload.get("move_ids") or payload.get("move_id"))
    if not move_ids:
        result = service_result(
            "RefineOdooInvoiceDescription",
            status="error",
            error="missing_move_id",
        )
        maybe_save_callback(
            request, instruction_row, result, description="Invoice refine missing move id"
        )
        return result

    outcomes = []
    pub = {}

    try:
        client, pub = _open_odoo_client(request, instruction_row, payload)
    except OdooRpcError as exc:
        logger.error("[RefineOdooInvoiceDescription] RPC auth: %s", exc)
        result = service_result(
            "RefineOdooInvoiceDescription",
            status="error",
            error=exc.status,
            detail=str(exc),
            move_ids=move_ids,
            odoo=pub,
            # Fail soft: posting already succeeded; do not raise.
            fail_soft=True,
        )
        maybe_save_callback(
            request, instruction_row, result, description="Invoice refine RPC auth failed"
        )
        return result
    except Exception as exc:
        logger.error("[RefineOdooInvoiceDescription] unexpected auth: %s", exc)
        result = service_result(
            "RefineOdooInvoiceDescription",
            status="error",
            error="error",
            detail=str(exc),
            move_ids=move_ids,
            odoo=pub,
            fail_soft=True,
        )
        maybe_save_callback(
            request, instruction_row, result, description="Invoice refine auth error"
        )
        return result

    for move_id in move_ids:
        outcomes.append(_refine_one(client, move_id, pub))

    any_changed = any(o.get("changed") for o in outcomes)
    any_error = any(o.get("status") == "error" for o in outcomes)
    status = "error" if any_error and not any_changed else "success"
    result = service_result(
        "RefineOdooInvoiceDescription",
        status=status,
        outcomes=outcomes,
        changed=any_changed,
        invoice_ref=_primary_ref(outcomes),
        move_ids=move_ids,
        odoo=pub,
        fail_soft=True,
    )
    maybe_save_callback(
        request,
        instruction_row,
        result,
        description=_callback_description(outcomes),
    )
    return result


def _queue_confirm(request, instruction_row, body: Any):
    """Publish the refine job. Do not read or rewrite the Confirm POST."""
    tenant = tenant_from_request(request)
    move_ids = _extract_move_ids(body)
    if not move_ids:
        result = service_result(
            "RefineOdooInvoiceDescription",
            status="skipped",
            reason="no_move_ids",
        )
        maybe_save_callback(
            request, instruction_row, result, description="Invoice refine skipped — no move id"
        )
        return result
    if tenant is None:
        result = service_result(
            "RefineOdooInvoiceDescription",
            status="error",
            error="no_tenant",
            move_ids=move_ids,
        )
        maybe_save_callback(
            request, instruction_row, result, description="Invoice refine no tenant"
        )
        return result

    from dose.webhook_events import publish_odoo_invoice_refine_event

    session = _cached_odoo_session(request)
    job = {
        "move_ids": move_ids,
        "source_path": getattr(request, "path", "") or "",
    }
    if session.get("odoo_session_id") and session.get("odoo_url"):
        job["odoo_session_id"] = session["odoo_session_id"]
        job["odoo_url"] = session["odoo_url"]
    published = publish_odoo_invoice_refine_event(tenant, job)
    if not published.get("success"):
        result = service_result(
            "RefineOdooInvoiceDescription",
            status="error",
            error=published.get("error") or "mailbox_enroll_failed",
            move_ids=move_ids,
            fail_soft=True,
        )
        maybe_save_callback(
            request, instruction_row, result, description="Invoice refine queue failed"
        )
        return result

    result = service_result(
        "RefineOdooInvoiceDescription",
        status="success",
        queued=True,
        move_ids=move_ids,
        mailbox_id=published.get("mailbox_id"),
        event_id=published.get("event_id"),
    )
    maybe_save_callback(
        request,
        instruction_row,
        result,
        description=f"Queued invoice Note refine for move(s) {move_ids}",
    )
    logger.info(
        "[RefineOdooInvoiceDescription] queued move_ids=%s mailbox=%s",
        move_ids,
        published.get("mailbox_id"),
    )
    return result


def _open_odoo_client(request, instruction_row, payload: dict):
    """Prefer the invoice-page session. Password login is only a fallback."""
    session_id = str(payload.get("odoo_session_id") or "").strip()
    session_url = str(payload.get("odoo_url") or "").rstrip("/")
    if not session_id or not session_url:
        live = _cached_odoo_session(request)
        session_id = session_id or live.get("odoo_session_id") or ""
        session_url = session_url or live.get("odoo_url") or ""
    if session_id and session_url:
        client = OdooRpcClient.for_session(session_url, session_id)
        pub = public_config({"url": session_url, "username": "session"})
        client.authenticate()
        return client, pub

    config = load_odoo_rpc_config(request=request, instruction_row=instruction_row)
    client = OdooRpcClient.from_config(config)
    client.authenticate()
    return client, public_config(config)


def _cached_odoo_session(request) -> dict:
    """Read the session passthrough already uses to show Odoo. Do not log it."""
    out = {"odoo_session_id": "", "odoo_url": ""}
    tenant = tenant_from_request(request)
    if tenant is None:
        return out
    try:
        from django.conf import settings

        from dose.models import TenantApp
        from dose.models.pass_through_endpoint import PassThroughEndpoint
        from dose.tenant_app_lookup import tenant_schema_search_path

        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                return out
            ta = (
                TenantApp.objects.filter(app_name="odoo", status="active")
                .order_by("-id")
                .first()
            )
            extra = ta.extra_config if ta and isinstance(ta.extra_config, dict) else {}
            out["odoo_session_id"] = str(extra.get("odoo_session_id") or "").strip()
            endpoint = (
                PassThroughEndpoint.objects.filter(slug="odoo", is_enabled=True)
                .order_by("-id")
                .first()
            )
            if endpoint is not None and getattr(endpoint, "endpoint_url", ""):
                out["odoo_url"] = str(endpoint.endpoint_url).rstrip("/")
            if not out["odoo_url"]:
                out["odoo_url"] = str(
                    extra.get("odoo_url") or getattr(ta, "app_url", "") or ""
                ).rstrip("/")
        if not out["odoo_url"]:
            out["odoo_url"] = str(getattr(settings, "ODOO_SHARED_URL", "") or "").rstrip("/")
    except Exception as exc:
        logger.warning("[RefineOdooInvoiceDescription] session lookup skipped: %s", exc)
    return out


def _is_mailbox_replay(request) -> bool:
    data = getattr(request, "mq_message_data", None) if request is not None else None
    if not isinstance(data, dict) or not data:
        return False
    nested = data.get("normalized_data")
    payload = nested if isinstance(nested, dict) and nested else data
    return bool(_coerce_move_ids(payload.get("move_ids") or payload.get("move_id")))


def _request_json(request) -> Any:
    raw = getattr(request, "body", b"") or b""
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="replace")
    else:
        text = str(raw)
    text = (text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"_raw": text[:2000]}


_ACTION_POST_RE = re.compile(r"action_post", re.I)
_ACCOUNT_MOVE_RE = re.compile(r"account\.move", re.I)


def _is_invoice_action_post(body: Any, path: str) -> bool:
    blob = path or ""
    if isinstance(body, dict):
        blob += " " + json.dumps(body, default=str)
    elif body:
        blob += " " + str(body)
    return bool(_ACTION_POST_RE.search(blob) and _ACCOUNT_MOVE_RE.search(blob))


def _extract_move_ids(body: Any) -> list[int]:
    """Best-effort parse of Odoo call_button / call_kw JSON-RPC bodies."""
    ids: list[int] = []

    def _take(value):
        if isinstance(value, int) and value > 0:
            ids.append(value)
        elif isinstance(value, list):
            for item in value:
                _take(item)
        elif isinstance(value, dict):
            for key in ("id", "res_id", "resId"):
                if key in value:
                    _take(value[key])

    if not isinstance(body, dict):
        return []

    params = body.get("params") if isinstance(body.get("params"), dict) else body
    if not isinstance(params, dict):
        return []

    args = params.get("args")
    if isinstance(args, list) and args:
        first = args[0]
        if isinstance(first, list):
            _take(first)
        else:
            _take(first)

    kwargs = params.get("kwargs") if isinstance(params.get("kwargs"), dict) else {}
    _take(kwargs.get("ids"))
    _take(params.get("ids"))
    _take(body.get("ids"))

    seen = set()
    out = []
    for mid in ids:
        if mid not in seen:
            seen.add(mid)
            out.append(mid)
    return out


def _refine_one(client: OdooRpcClient, move_id: int, pub: dict) -> dict:
    try:
        rows = client.execute_kw(
            "account.move",
            "read",
            [[move_id]],
            {"fields": ["id", "name", "narration", "state", "move_type"]},
        )
    except Exception as exc:
        logger.error("[RefineOdooInvoiceDescription] read failed move=%s: %s", move_id, exc)
        return {
            "status": "error",
            "move_id": move_id,
            "error": "read_failed",
            "detail": str(exc),
            "changed": False,
            "fail_soft": True,
        }

    if not rows:
        return {
            "status": "error",
            "move_id": move_id,
            "error": "move_not_found",
            "changed": False,
            "fail_soft": True,
        }

    row = rows[0] if isinstance(rows, list) else rows
    before = (row.get("narration") or "") if isinstance(row, dict) else ""
    if isinstance(before, bool):
        before = ""
    before = str(before)
    invoice_name = ""
    if isinstance(row, dict):
        invoice_name = str(row.get("name") or "") or f"#{move_id}"

    changed = False
    after = before
    line_outcomes = []
    reason = ""
    ai_detail = ""

    # Header narration (Terms / Note)
    if len(before.strip()) >= _MIN_LEN:
        try:
            cleaned = _ai_clean(before)
            cleaned = (cleaned or "").strip() or before
            if _text_hash(cleaned) != _text_hash(before):
                client.execute_kw(
                    "account.move",
                    "write",
                    [[move_id], {"narration": cleaned}],
                )
                after = cleaned
                changed = True
            else:
                reason = "no_change"
        except Exception as exc:
            logger.warning(
                "[RefineOdooInvoiceDescription] narration AI/write failed move=%s: %s",
                move_id,
                exc,
            )
            reason = "ai_failed_soft"
            ai_detail = _public_error(exc)
    else:
        reason = "empty_or_short"

    # Line notes from "Add a note" (display_type line_note / note)
    try:
        note_lines = client.execute_kw(
            "account.move.line",
            "search_read",
            [[("move_id", "=", move_id), ("display_type", "in", ["line_note", "note"])]],
            {"fields": ["id", "name", "display_type"]},
        )
    except Exception as exc:
        logger.warning(
            "[RefineOdooInvoiceDescription] note lines read failed move=%s: %s",
            move_id,
            exc,
        )
        note_lines = []

    for line in note_lines or []:
        if not isinstance(line, dict):
            continue
        line_id = line.get("id")
        line_before = str(line.get("name") or "")
        if not line_id or len(line_before.strip()) < _MIN_LEN:
            continue
        try:
            line_after = _ai_clean(line_before)
            line_after = (line_after or "").strip() or line_before
            if _text_hash(line_after) == _text_hash(line_before):
                line_outcomes.append(
                    {
                        "line_id": line_id,
                        "before": line_before,
                        "after": line_before,
                        "changed": False,
                    }
                )
                continue
            client.execute_kw(
                "account.move.line",
                "write",
                [[line_id], {"name": line_after}],
            )
            changed = True
            line_outcomes.append(
                {
                    "line_id": line_id,
                    "before": line_before,
                    "after": line_after,
                    "changed": True,
                }
            )
        except Exception as exc:
            logger.warning(
                "[RefineOdooInvoiceDescription] note line %s failed: %s",
                line_id,
                exc,
            )
            if not ai_detail:
                ai_detail = _public_error(exc)
            line_outcomes.append(
                {
                    "line_id": line_id,
                    "before": line_before,
                    "after": line_before,
                    "changed": False,
                    "error": _public_error(exc),
                    "fail_soft": True,
                }
            )

    line_ai_failed = any(isinstance(lo, dict) and lo.get("error") for lo in line_outcomes)
    if changed:
        reason = "refined"
    elif line_ai_failed:
        reason = "ai_failed_soft"
    elif line_outcomes and not reason:
        reason = "no_change"

    if not changed and reason == "empty_or_short" and not line_outcomes:
        return {
            "status": "success",
            "move_id": move_id,
            "invoice_name": invoice_name,
            "before": before,
            "after": before,
            "changed": False,
            "reason": "empty_or_short",
            "line_notes": [],
        }

    outcome = {
        "status": "success",
        "move_id": move_id,
        "invoice_name": invoice_name,
        "before": before,
        "after": after,
        "changed": changed,
        "reason": reason,
        "model": "account.move",
        "field": "narration",
        "line_notes": line_outcomes,
        "before_hash": _text_hash(before),
        "after_hash": _text_hash(after),
        "odoo": pub,
        "fail_soft": True,
    }
    if ai_detail:
        outcome["detail"] = ai_detail
    return outcome


def _public_error(exc: BaseException) -> str:
    """Short error for the green bar. Do not include the invoice note."""
    text = " ".join(str(exc or "").split())
    if len(text) > 180:
        text = text[:179].rstrip() + "…"
    return text


def _ai_clean(text: str) -> str:
    from django.conf import settings

    from llm_router.providers import complete_chat
    from llm_router.router import RoutePlan

    # Short notes classify as "lite" and were sent to retired Haiku 3.5 (404).
    plan = RoutePlan(
        provider=getattr(settings, "LLM_ROUTER_STANDARD_PROVIDER", "anthropic"),
        model=getattr(settings, "LLM_ROUTER_STANDARD_MODEL", "claude-sonnet-4-6"),
        task_bucket="standard",
        user_tier="standard",
        reason="invoice_note_refine",
    )
    import requests

    try:
        out = complete_chat(
            plan,
            messages=[{"role": "user", "content": text}],
            system_prompt=REFINE_SYSTEM_PROMPT,
            max_tokens=1024,
            timeout=45,
        )
    except requests.HTTPError as exc:
        resp = getattr(exc, "response", None)
        status = getattr(resp, "status_code", "?")
        body = ""
        if resp is not None:
            body = " ".join((getattr(resp, "text", "") or "").split())[:160]
        raise RuntimeError(f"AI HTTP {status}: {body}") from exc
    cleaned = (out or "").strip()
    # Provider misconfig returns bracketed status strings — treat as soft fail.
    if cleaned.startswith("[llm_router]"):
        raise RuntimeError(cleaned)
    # Strip accidental wrapping quotes
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in "\"'":
        cleaned = cleaned[1:-1].strip()
    return cleaned


def _extract_payload(request, instruction_row) -> dict:
    data = getattr(request, "mq_message_data", None) if request is not None else None
    if isinstance(data, dict) and data:
        nested = data.get("normalized_data")
        if isinstance(nested, dict) and nested:
            return dict(nested)
        return dict(data)
    if request is not None:
        body = getattr(request, "body", b"") or b""
        if isinstance(body, bytes):
            text = body.decode("utf-8", errors="replace")
        else:
            text = str(body)
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return {}


def _coerce_move_ids(raw) -> list[int]:
    if raw is None:
        return []
    if isinstance(raw, int):
        return [raw] if raw > 0 else []
    if isinstance(raw, str) and raw.strip().isdigit():
        return [int(raw.strip())]
    if isinstance(raw, list):
        out = []
        for item in raw:
            out.extend(_coerce_move_ids(item))
        return out
    return []


def _text_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _primary_ref(outcomes: list[dict]) -> str:
    for o in outcomes:
        name = o.get("invoice_name") or ""
        if name:
            return name
        if o.get("move_id"):
            return f"#{o['move_id']}"
    return ""


def _callback_description(outcomes: list[dict]) -> str:
    changed = [o for o in outcomes if o.get("changed")]
    if changed:
        refs = ", ".join(
            str(o.get("invoice_name") or o.get("move_id")) for o in changed[:3]
        )
        return f"Invoice description refined: {refs}"
    if outcomes and all(o.get("reason") == "no_change" for o in outcomes):
        return "Invoice description refine: no change"
    return "Invoice description refine"
