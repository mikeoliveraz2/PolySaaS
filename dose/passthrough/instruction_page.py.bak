"""Generic passthrough: serve an atomic response when an Instruction matches.

GET: HTML replacement page. POST: JSON (or HTML) from the same Instruction →
atomic path. Applies equally to every passthrough endpoint — no app name or
path hardcoding. Matching is data-driven from tenant-schema Instruction rows
via find_matching_instructions (same rules as the orchestration bar).

Owner-approved 2026-09-24: Slice 1 New Vendor Assist must prove dynamic
orchestration (Instruction → Atomic → page), not handler path special-cases.
Slice 2: POST on the same document path is a follow-up step, not a handler
hardcode.
"""
from __future__ import annotations

import logging

import json

from django.http import HttpResponse, JsonResponse

logger = logging.getLogger(__name__)

# Generic document-GET bypass: skip replacement and forward to upstream.
_SKIP_REPLACEMENT_QUERY = "polysaas_odoo_form"


def _upstream_subpath_from_request(request) -> str:
    """Extract upstream path under /pt/admin|<dose>/<slug>/..."""
    import re

    path_only = (getattr(request, "path_info", "") or "").split("?")[0]
    match = re.match(r"^/pt/(?:admin|dose)/[^/]+(.*)$", path_only)
    sub = (match.group(1) if match else "") or "/"
    if not sub.startswith("/"):
        sub = "/" + sub
    return sub.rstrip("/") or "/"


def _skip_replacement(request) -> bool:
    return (request.GET.get(_SKIP_REPLACEMENT_QUERY) or "").strip() == "1"


def _in_page_step_from_request(request) -> str:
    """Return JSON `step` when this POST is an in-page atomic follow-up."""
    raw = getattr(request, "body", b"") or b""
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="replace").strip()
    else:
        text = str(raw).strip()
    if not text:
        return ""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError, TypeError):
        return ""
    if not isinstance(data, dict):
        return ""
    return str(data.get("step") or "").strip()


def _unmatched_post_step_response(request, path: str):
    """JSON 404 so the page never silently forwards an Assist POST to Odoo."""
    step = _in_page_step_from_request(request)
    if not step:
        return None
    print(
        f"[INSTRUCTION-PAGE] no POST Instruction for {path!r} "
        f"(in-page step={step!r})"
    )
    return JsonResponse(
        {
            "status": "error",
            "message": (
                "No matching POST instruction for this path. "
                "Find suppliers needs a POST REQ Instruction on the same path."
            ),
            "step": step,
        },
        status=404,
    )


def document_path_matches_instruction(upstream_path: str, instruction_path: str) -> bool:
    """
    True when this document GET should run the Instruction's page atomic.

    find_matching_instructions also treats a *shorter* URL as a match for a
    longer rule (e.g. /odoo vs /odoo/vendors/new) for orchestration bucketing.
    That must not replace the Odoo shell — only the rule path (or a deeper
    path under it) may select a replacement page.
    """
    rule = ((instruction_path or "").split("?")[0].split("#")[0].rstrip("/") or "").lower()
    norm = ((upstream_path or "").split("?")[0].split("#")[0].rstrip("/") or "").lower()
    if not rule or not norm or rule == "/":
        return False
    if not norm.startswith("/"):
        norm = "/" + norm
    if not rule.startswith("/"):
        rule = "/" + rule
    if norm == rule:
        return True
    if norm.startswith(rule + "/"):
        return True
    # contains: rule appears as a contiguous path in the document URL
    if rule in norm:
        return True
    return False


def _html_from_atomic_result(result) -> tuple[str | None, str]:
    """Return (html, content_type) when the atomic built a replacement page."""
    if result is None:
        return None, ""
    if isinstance(result, HttpResponse):
        ct = result.get("Content-Type", "text/html; charset=utf-8")
        if "text/html" not in (ct or ""):
            return None, ""
        try:
            return result.content.decode("utf-8", errors="replace"), ct
        except Exception:
            return None, ""
    if not isinstance(result, dict):
        return None, ""
    html = result.get("html") or result.get("page_html")
    if not html or not isinstance(html, str):
        return None, ""
    ct = result.get("content_type") or "text/html; charset=utf-8"
    return html, ct


def _json_from_atomic_result(result) -> dict | None:
    """Return a JSON-serializable dict when the atomic answered a follow-up POST."""
    if result is None or not isinstance(result, dict):
        return None
    if result.get("html") or result.get("page_html"):
        return None
    if result.get("json_response") is True or result.get("returns_json") is True:
        payload = {
            key: val
            for key, val in result.items()
            if key not in ("wrap_passthrough", "json_response", "returns_json", "html", "page_html")
        }
        return payload
    return None


def try_instruction_page_response(request, endpoint, handler, trigger, upstream_path=None):
    """
    If the request matches an Instruction whose atomic returns HTML or JSON,
    return that response.

    GET serves a replacement page. POST runs the same instruction/atomic path
    for in-page steps (e.g. criteria capture) without forwarding upstream.

    Returns HttpResponse or None to continue normal upstream forwarding.
    """
    method = (getattr(request, "method", "GET") or "GET").upper()
    if method not in ("GET", "POST"):
        return None
    if method == "GET" and _skip_replacement(request):
        return None

    path = upstream_path or getattr(request, "_passthrough_upstream_path", None)
    if not path:
        path = _upstream_subpath_from_request(request)
    if not path or path in ("/", ""):
        return None

    tenant = getattr(request, "tenant", None)
    if not tenant:
        try:
            from dose.utils import get_current_tenant

            tenant = get_current_tenant(request)
        except Exception:
            tenant = None
    if not tenant:
        return None

    try:
        from dose.passthrough.orchestration_hook import find_matching_instructions
        from dose.services.atomic_services_registry import (
            get_atomic_service,
            init_atomic_services_registry,
            normalize_executescript_value,
        )
    except Exception as exc:
        logger.warning("[INSTRUCTION-PAGE] import failed: %s", exc)
        return None

    matched = find_matching_instructions(tenant, path, method=method, direction="REQ")
    if not matched:
        print(f"[INSTRUCTION-PAGE] no Instruction match for {method} {path!r}")
        if method == "POST":
            unmatched = _unmatched_post_step_response(request, path)
            if unmatched is not None:
                return unmatched
        return None

    page_matched = [
        row
        for row in matched
        if document_path_matches_instruction(
            path, getattr(row, "requestpath", None) or ""
        )
    ]
    if not page_matched:
        print(
            f"[INSTRUCTION-PAGE] orch matched {len(matched)} row(s) for {path!r} "
            f"but none are document-path matches (skip replace; avoid /odoo "
            f"stealing /odoo/vendors/new)"
        )
        if method == "POST":
            unmatched = _unmatched_post_step_response(request, path)
            if unmatched is not None:
                return unmatched
        return None

    init_atomic_services_registry()
    tenant_name = getattr(tenant, "schema_name", None)

    for instruction_row in page_matched:
        executescript_name = normalize_executescript_value(
            getattr(instruction_row, "executescript", None) or ""
        )
        if not executescript_name:
            continue
        cls = get_atomic_service(executescript_name, tenant_name=tenant_name)
        if not cls or not hasattr(cls, "execute_and_save"):
            logger.warning(
                "[INSTRUCTION-PAGE] service not found: %s (instruction %s)",
                executescript_name,
                getattr(instruction_row, "id", "?"),
            )
            continue
        try:
            result = cls.execute_and_save(request, instruction_row)
        except Exception as exc:
            logger.exception(
                "[INSTRUCTION-PAGE] %s failed: %s", executescript_name, exc
            )
            continue

        json_payload = _json_from_atomic_result(result)
        if json_payload is not None:
            print(
                f"[INSTRUCTION-PAGE] Serving atomic JSON for {method} {path!r} "
                f"via {executescript_name} (instruction "
                f"{getattr(instruction_row, 'id', '?')})"
            )
            request._passthrough_upstream_path = path
            status_code = 200
            if json_payload.get("status") in ("error", "failed"):
                status_code = 400
            return JsonResponse(json_payload, status=status_code)

        html, content_type = _html_from_atomic_result(result)
        if not html:
            continue

        print(
            f"[INSTRUCTION-PAGE] Serving atomic HTML for {path!r} "
            f"via {executescript_name} (instruction "
            f"{getattr(instruction_row, 'id', '?')})"
        )
        request._passthrough_upstream_path = path
        response = HttpResponse(html, content_type=content_type)
        wrap = True
        if isinstance(result, dict) and result.get("wrap_passthrough") is False:
            wrap = False
        if wrap:
            try:
                from dose.passthrough.forwarding import _wrap_in_admin_template

                return _wrap_in_admin_template(
                    request, response, trigger, endpoint, handler=handler
                )
            except Exception as wrap_exc:
                logger.warning("[INSTRUCTION-PAGE] wrap failed: %s", wrap_exc)
        return response

    return None
