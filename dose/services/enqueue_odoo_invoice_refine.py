"""Enqueue Odoo invoice refine after passthrough action_post (async mailbox).

Runs on the passthrough orchestration hook (RES preferred). Filters to
account.move + action_post, then publishes a trigger envelope so the mailbox
consumer can run RefineOdooInvoiceDescription without holding the HTTP response.
"""
from __future__ import annotations

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

logger = logging.getLogger(__name__)

_ACTION_POST_RE = re.compile(r"action_post", re.I)
_ACCOUNT_MOVE_RE = re.compile(r"account\.move", re.I)


class EnqueueOdooInvoiceRefine(AtomicServiceBase):
    atomic_apps = ("odoo",)
    atomic_category = "write"

    @staticmethod
    def get_parameters(parameters, key="EnqueueOdooInvoiceRefine"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        tenant = tenant_from_request(request)
        body = _request_json(request)
        if not _is_invoice_action_post(body, getattr(request, "path", "") or ""):
            result = service_result(
                "EnqueueOdooInvoiceRefine",
                status="skipped",
                reason="not_account_move_action_post",
            )
            return result

        move_ids = _extract_move_ids(body)
        if not move_ids:
            result = service_result(
                "EnqueueOdooInvoiceRefine",
                status="skipped",
                reason="no_move_ids",
            )
            maybe_save_callback(
                request, instruction_row, result, description="Invoice refine enqueue skipped"
            )
            return result

        if tenant is None:
            result = service_result(
                "EnqueueOdooInvoiceRefine",
                status="error",
                error="no_tenant",
            )
            maybe_save_callback(
                request, instruction_row, result, description="Invoice refine enqueue no tenant"
            )
            return result

        from dose.webhook_events import publish_odoo_invoice_refine_event

        published = publish_odoo_invoice_refine_event(
            tenant,
            {
                "move_ids": move_ids,
                "source_path": getattr(request, "path", "") or "",
            },
        )
        if not published.get("success"):
            result = service_result(
                "EnqueueOdooInvoiceRefine",
                status="error",
                error=published.get("error") or "mailbox_enroll_failed",
                move_ids=move_ids,
            )
            maybe_save_callback(
                request, instruction_row, result, description="Invoice refine enqueue failed"
            )
            return result

        result = service_result(
            "EnqueueOdooInvoiceRefine",
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
            description=f"Queued invoice refine for move(s) {move_ids}",
        )
        logger.info(
            "[EnqueueOdooInvoiceRefine] queued move_ids=%s mailbox=%s",
            move_ids,
            published.get("mailbox_id"),
        )
        return result


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

    # call_button / call_kw: args often [[ids], ...]
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

    # Deduplicate preserving order
    seen = set()
    out = []
    for mid in ids:
        if mid not in seen:
            seen.add(mid)
            out.append(mid)
    return out
