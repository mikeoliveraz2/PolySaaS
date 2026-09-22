"""Refine Odoo invoice narration mid-stream via AI (Type 3).

Mailbox consumer atomic:
  read account.move.narration → AI clean → write back if changed.

Guardrails:
  - Tenant schema on every ORM/RPC
  - Idempotent: skip write when cleaned equals current (no refine loop)
  - Fail soft: AI/RPC errors leave Odoo text untouched
  - Field: narration only (v1)
  - PII: send narration text only to the LLM
"""
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

        config = load_odoo_rpc_config(request=request, instruction_row=instruction_row)
        pub = public_config(config)
        outcomes = []

        try:
            client = OdooRpcClient.from_config(config)
            client.authenticate()
        except OdooRpcError as exc:
            logger.error("[RefineOdooInvoiceDescription] RPC auth: %s", exc)
            result = service_result(
                "RefineOdooInvoiceDescription",
                status="error",
                error=exc.status,
                detail=str(exc),
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

    if len(before.strip()) < _MIN_LEN:
        return {
            "status": "success",
            "move_id": move_id,
            "invoice_name": invoice_name,
            "before": before,
            "after": before,
            "changed": False,
            "reason": "empty_or_short",
        }

    try:
        after = _ai_clean(before)
    except Exception as exc:
        logger.warning("[RefineOdooInvoiceDescription] AI failed move=%s: %s", move_id, exc)
        return {
            "status": "success",
            "move_id": move_id,
            "invoice_name": invoice_name,
            "before": before,
            "after": before,
            "changed": False,
            "reason": "ai_failed_soft",
            "detail": str(exc),
            "fail_soft": True,
        }

    after = (after or "").strip() or before
    if _text_hash(after) == _text_hash(before):
        return {
            "status": "success",
            "move_id": move_id,
            "invoice_name": invoice_name,
            "before": before,
            "after": before,
            "changed": False,
            "reason": "no_change",
        }

    try:
        client.execute_kw(
            "account.move",
            "write",
            [[move_id], {"narration": after}],
        )
    except Exception as exc:
        logger.error("[RefineOdooInvoiceDescription] write failed move=%s: %s", move_id, exc)
        return {
            "status": "error",
            "move_id": move_id,
            "invoice_name": invoice_name,
            "before": before,
            "after": after,
            "changed": False,
            "error": "write_failed",
            "detail": str(exc),
            "fail_soft": True,
        }

    return {
        "status": "success",
        "move_id": move_id,
        "invoice_name": invoice_name,
        "before": before,
        "after": after,
        "changed": True,
        "model": "account.move",
        "field": "narration",
        "before_hash": _text_hash(before),
        "after_hash": _text_hash(after),
        "odoo": pub,
    }


def _ai_clean(text: str) -> str:
    from llm_router.providers import complete_chat
    from llm_router.router import route

    plan = route(prompt=text, user_tier="standard", task_hint="chat")
    out = complete_chat(
        plan,
        messages=[{"role": "user", "content": text}],
        system_prompt=REFINE_SYSTEM_PROMPT,
        max_tokens=1024,
        timeout=45,
    )
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
