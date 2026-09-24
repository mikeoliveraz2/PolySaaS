"""New Vendor Assist atomic: branded page (Slice 1) + criteria capture (Slice 2).

Triggered by tenant-schema Instructions matching GET/POST /odoo/vendors/new.
The Odoo passthrough handler must not hardcode that path; instruction matching does.
"""
from __future__ import annotations

import json
import logging

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import (
    maybe_save_callback,
    service_result,
    tenant_from_request,
)
from dose.services.atomic_services_registry import filter_parameters_for_service

logger = logging.getLogger(__name__)

VENDOR_PAGE_TITLE = "New Vendor (PolySaaS Assist)"
VENDOR_PAGE_LOADED_MESSAGE = "Vendor page loaded"
CRITERIA_CAPTURED_MESSAGE = "Criteria captured"
CRITERIA_CAPTURE_FAILED_MESSAGE = "Vendor criteria capture failed"
CRITERIA_SESSION_KEY = "odoo_vendor_assist_criteria"
CRITERIA_CAPTURE_STEP = "capture_criteria"

DEFAULT_PRODUCT_LINE = "Packaging film"
DEFAULT_REGION = "Southeast Asia"
DEFAULT_PRICE_RANGE = "Under $2 per unit"


class OdooVendorAssist(AtomicServiceBase):
    """Build the New Vendor Assist page and record in-page steps (criteria)."""

    atomic_apps = ("odoo",)
    atomic_category = "ui"
    returns_passthrough_page = True

    @staticmethod
    def get_parameters(parameters, key="OdooVendorAssist"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        if _is_criteria_capture_request(request):
            return capture_vendor_criteria(request, instruction_row)

        # Orchestration bar POST /dose/api/orchestration-navigate/ only needs a match
        # count. Full HTML is served on document GET via instruction_page — rendering
        # admin chrome here was heavy and could surface as gateway 502 on the bar.
        if getattr(request, "_orch_navigate_api", False) or (
            "/dose/api/orchestration-navigate" in (getattr(request, "path_info", "") or "")
        ):
            emit_vendor_page_loaded(request)
            result = service_result(
                "OdooVendorAssist",
                status="success",
                matched_only=True,
                message=VENDOR_PAGE_LOADED_MESSAGE,
            )
            maybe_save_callback(
                request,
                instruction_row,
                {
                    "status": "success",
                    "matched_only": True,
                    "message": VENDOR_PAGE_LOADED_MESSAGE,
                },
                description="New Vendor Assist matched on navigate (page deferred)",
            )
            return result

        emit_vendor_page_loaded(request)
        html = render_vendor_assist_html(request)
        result = service_result(
            "OdooVendorAssist",
            status="success",
            html=html,
            content_type="text/html; charset=utf-8",
            wrap_passthrough=True,
            page_title=VENDOR_PAGE_TITLE,
            message=VENDOR_PAGE_LOADED_MESSAGE,
        )
        maybe_save_callback(
            request,
            instruction_row,
            {
                "status": "success",
                "page_title": VENDOR_PAGE_TITLE,
                "message": VENDOR_PAGE_LOADED_MESSAGE,
            },
            description="New Vendor Assist page served",
        )
        return result


def _request_payload(request) -> dict:
    """Parse JSON body or form POST. Never raises."""
    raw = getattr(request, "body", b"") or b""
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="replace").strip()
    else:
        text = str(raw).strip()
    if text:
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    post = getattr(request, "POST", None)
    if post:
        return {key: post.get(key) for key in post}
    return {}


def _is_criteria_capture_request(request) -> bool:
    method = (getattr(request, "method", "GET") or "GET").upper()
    if method != "POST":
        return False
    if "/dose/api/orchestration-navigate" in (getattr(request, "path_info", "") or ""):
        payload = _request_payload(request)
        step = str(payload.get("step") or "").strip()
        return step == CRITERIA_CAPTURE_STEP
    return True


def capture_vendor_criteria(request, instruction_row):
    """Slice 2: record product line / region / price range and toast."""
    payload = _request_payload(request)
    product_line = str(payload.get("product_line") or payload.get("product") or "").strip()
    region = str(payload.get("region") or "").strip()
    price_range = str(
        payload.get("price_range") or payload.get("price") or ""
    ).strip()
    criteria = {
        "product_line": product_line,
        "region": region,
        "price_range": price_range,
    }
    missing = [name for name, val in criteria.items() if not val]
    if missing:
        detail = f"{CRITERIA_CAPTURE_FAILED_MESSAGE}: missing {', '.join(missing)}"
        emit_vendor_step_message(request, detail, level="error")
        result = service_result(
            "OdooVendorAssist",
            status="error",
            json_response=True,
            wrap_passthrough=False,
            message=detail,
            criteria=criteria,
        )
        maybe_save_callback(
            request,
            instruction_row,
            {"status": "error", "message": detail, "criteria": criteria},
            description="New Vendor Assist criteria capture failed",
        )
        return result

    session = getattr(request, "session", None)
    if session is not None:
        try:
            session[CRITERIA_SESSION_KEY] = criteria
            if hasattr(session, "modified"):
                session.modified = True
        except Exception:
            logger.warning("[OdooVendorAssist] could not store criteria in session")

    emit_vendor_step_message(request, CRITERIA_CAPTURED_MESSAGE, level="success")
    result = service_result(
        "OdooVendorAssist",
        status="success",
        json_response=True,
        wrap_passthrough=False,
        message=CRITERIA_CAPTURED_MESSAGE,
        criteria=criteria,
    )
    maybe_save_callback(
        request,
        instruction_row,
        {
            "status": "success",
            "message": CRITERIA_CAPTURED_MESSAGE,
            "criteria": criteria,
        },
        description="New Vendor Assist criteria captured",
    )
    return result


def emit_vendor_page_loaded(request) -> None:
    """Create a tenant-schema DoseMessage so the passthrough green bar can show it."""
    emit_vendor_step_message(request, VENDOR_PAGE_LOADED_MESSAGE, level="success")


def emit_vendor_step_message(request, message: str, level: str = "info") -> None:
    """Each atomic step reports success or failure via DoseMessage (tenant schema)."""
    from dose.messaging import create_dose_message

    tenant = tenant_from_request(request)
    if not tenant:
        logger.warning("[OdooVendorAssist] no tenant; skip DoseMessage")
        return
    user = getattr(request, "user", None)
    create_dose_message(
        tenant=tenant,
        user=user,
        message=message,
        level=level,
    )


def _criteria_from_session(request) -> dict:
    session = getattr(request, "session", None) or {}
    stored = session.get(CRITERIA_SESSION_KEY) if hasattr(session, "get") else None
    if isinstance(stored, dict):
        return {
            "product_line": stored.get("product_line") or DEFAULT_PRODUCT_LINE,
            "region": stored.get("region") or DEFAULT_REGION,
            "price_range": stored.get("price_range") or DEFAULT_PRICE_RANGE,
        }
    return {
        "product_line": DEFAULT_PRODUCT_LINE,
        "region": DEFAULT_REGION,
        "price_range": DEFAULT_PRICE_RANGE,
    }


def render_vendor_assist_html(request) -> str:
    """Branded shell HTML with criteria fields (search/save still stubs)."""
    from django.template.loader import render_to_string

    ctx = {"page_title": VENDOR_PAGE_TITLE}
    ctx.update(_criteria_from_session(request))
    return render_to_string(
        "admin/odoo_vendor_lookup.html",
        ctx,
        request=request,
    )
