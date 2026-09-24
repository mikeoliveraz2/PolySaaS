"""Slice 1 — New Vendor Assist atomic: branded replacement page (no AI / RPC / events).

Triggered by a tenant-schema Instruction matching GET /odoo/vendors/new.
The Odoo passthrough handler must not hardcode that path; instruction matching does.
"""
from __future__ import annotations

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


class OdooVendorAssist(AtomicServiceBase):
    """Build and return the New Vendor Assist shell HTML."""

    atomic_apps = ("odoo",)
    atomic_category = "ui"
    returns_passthrough_page = True

    @staticmethod
    def get_parameters(parameters, key="OdooVendorAssist"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
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


def emit_vendor_page_loaded(request) -> None:
    """Create a tenant-schema DoseMessage so the passthrough green bar can show it."""
    from dose.messaging import create_dose_message

    tenant = tenant_from_request(request)
    if not tenant:
        logger.warning("[OdooVendorAssist] no tenant; skip DoseMessage")
        return
    user = getattr(request, "user", None)
    create_dose_message(
        tenant=tenant,
        user=user,
        message=VENDOR_PAGE_LOADED_MESSAGE,
        level="success",
    )


def render_vendor_assist_html(request) -> str:
    """Branded Slice 1 shell HTML (criteria + manual form stubs only)."""
    from django.template.loader import render_to_string

    return render_to_string(
        "admin/odoo_vendor_lookup.html",
        {"page_title": VENDOR_PAGE_TITLE},
        request=request,
    )
