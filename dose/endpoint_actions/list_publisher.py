# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Unified Endpoint Workspace — 2026-09-01

"""One direct_event publisher for every vendor list bookmark.

Replaces five near-identical ``_publish_list_*`` functions (three in
``odoo.py``, two in ``hubspot.py``) that differed only by service class, row
key, and noun. Each adapter now declares a ``ListSpec`` instead of repeating
the tenant guard, request shim, result unpacking, and return dict.

The legacy per-vendor keys are still emitted alongside ``envelope`` so the
current browser renderer keeps working until it is switched over.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Callable

from dose.endpoint_data.envelope import (
    build_envelope,
    count_detail,
    error_envelope,
    legacy_key_for,
)
from dose.passthrough.orchestration_log import ensure_tenant_search_path


@dataclass(frozen=True)
class ListSpec:
    """Everything that used to differ between the copied publishers."""

    action_path: str
    object_type: str
    vendor_key: str
    search_path_label: str
    callback_description: str
    error_message: str
    load_service: Callable
    rows_key: str = ""
    # Adapters pass their own module-scoped guard so the search-path check stays
    # patchable at the adapter module, where the existing tests target it.
    guard: Callable | None = None

    @property
    def result_rows_key(self) -> str:
        """Key the Atomic Service uses for its rows (invoices/contacts/sales)."""
        return self.rows_key or legacy_key_for(self.object_type)


def list_limit_payload(supplied: dict) -> dict:
    """Direct event needs no form fields; ignore unknown keys quietly."""
    if not isinstance(supplied, dict):
        return {}
    limit = supplied.get("limit")
    if limit in (None, ""):
        return {}
    try:
        return {"limit": max(1, min(int(limit), 200))}
    except (TypeError, ValueError):
        return {}


def _guard_failure(spec: ListSpec, reason: str) -> dict:
    return {
        "success": False,
        "error": reason,
        "envelope": error_envelope(spec.object_type, reason, error=reason),
    }


def publish_list(tenant, payload: dict, spec: ListSpec) -> dict:
    """Run the spec's Atomic Service, persist CallBackData, return the envelope."""
    if not tenant or not getattr(tenant, "schema_name", None):
        return _guard_failure(spec, "no tenant")
    guard = spec.guard or ensure_tenant_search_path
    if not guard(tenant, spec.search_path_label):
        return _guard_failure(spec, "invalid tenant schema")

    request = SimpleNamespace(
        tenant=tenant,
        mq_message_data=dict(payload or {}),
        body=b"{}",
        atomic_parameters=[],
        user=None,
    )
    result = spec.load_service().execute_and_save(request, None)

    ok = result.get("status") == "success"
    count = int(result.get("count") or 0)
    rows_key = spec.result_rows_key
    raw_rows = result.get(rows_key)
    rows = raw_rows if isinstance(raw_rows, list) else []

    if ok:
        detail = count_detail(spec.object_type, count)
    else:
        detail = result.get("detail") or result.get("error") or spec.error_message

    vendor_block = result.get(spec.vendor_key)
    if not isinstance(vendor_block, dict):
        vendor_block = {}

    if ok:
        envelope = build_envelope(
            spec.object_type,
            status="success",
            rows=rows,
            detail=detail,
        )
    else:
        envelope = error_envelope(
            spec.object_type,
            detail,
            error=result.get("error") or "error",
        )

    return {
        "success": ok,
        "sync": True,
        "status": result.get("status"),
        "count": count,
        "detail": detail,
        "action_path": spec.action_path,
        "list_kind": legacy_key_for(spec.object_type),
        "error": None if ok else detail,
        "callback_id": result.get("callback_id"),
        "callback_description": result.get("callback_description")
        or spec.callback_description,
        "matching_event_key": result.get("matching_event_key") or spec.action_path,
        spec.vendor_key: vendor_block,
        # Deprecated: superseded by envelope.rows, kept for one release.
        rows_key: rows,
        "envelope": envelope,
        "popup": "callback_record",
    }


def make_publisher(spec: ListSpec) -> Callable:
    """Bind a spec into the ``publish(tenant, payload)`` shape adapters expect."""

    def _publish(tenant, payload: dict) -> dict:
        return publish_list(tenant, payload, spec)

    return _publish
