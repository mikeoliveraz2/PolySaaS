"""Fetch HubSpot deals (sales) into CallBackData (endpoint-home bookmark)."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from __future__ import annotations

import logging
import re
from datetime import datetime

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import service_result
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.hubspot_api import HubspotApiError, HubspotApiService, HubspotNotConnected

logger = logging.getLogger(__name__)

# HubSpotCreateDeal description: "Sale from Slack for Big Guys Warehouse (Moon Rocks)"
_PARTNER_IN_DESC = re.compile(r"\(([^)]+)\)\s*$")


class HubSpotListSales(AtomicServiceBase):
    atomic_apps = ("hubspot",)
    atomic_category = "read"

    @staticmethod
    def get_parameters(parameters, key="HubSpotListSales"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row=None):
        limit = _limit_from(request, instruction_row)
        tenant = getattr(request, "tenant", None)
        hubspot_meta = {}
        try:
            api = HubspotApiService.for_tenant(tenant)
            hubspot_meta = {
                "portal_id": (api._extra().get("hs_portal_id") or ""),
                "token_type": (api._extra().get("hs_token_type") or ""),
            }
            raw = api.list_deals(limit=limit)
        except HubspotNotConnected as exc:
            return service_result(
                "HubSpotListSales",
                status="error",
                error="not_connected",
                detail=str(exc),
                hubspot=hubspot_meta,
            )
        except HubspotApiError as exc:
            logger.error("[HubSpotListSales] %s", exc)
            return service_result(
                "HubSpotListSales",
                status="error",
                error="api_error",
                detail=str(exc),
                hubspot=hubspot_meta,
            )
        except Exception as exc:
            logger.error("[HubSpotListSales] unexpected: %s", exc)
            return service_result(
                "HubSpotListSales",
                status="error",
                error="error",
                detail=str(exc),
                hubspot=hubspot_meta,
            )

        sales = [_normalize_deal_row(row) for row in (raw or [])]
        sales.sort(key=lambda r: r.get("_sort") or "", reverse=True)
        for row in sales:
            row.pop("_sort", None)

        result = service_result(
            "HubSpotListSales",
            status="success",
            count=len(sales),
            sales=sales,
            hubspot=hubspot_meta,
        )
        callback_row = _force_save_callback(request, instruction_row, result)
        if callback_row is not None:
            result["callback_id"] = getattr(callback_row, "id", None)
            result["callback_description"] = getattr(
                callback_row, "description", None
            ) or "HubSpot sales/deals list (bookmark capture)"
            result["matching_event_key"] = getattr(
                callback_row, "matchingEventKey", None
            ) or "hubspot.list_sales"
        return result


def _normalize_deal_row(row: dict) -> dict:
    description = str(row.get("description") or "").strip()
    partner = ""
    match = _PARTNER_IN_DESC.search(description)
    if match:
        partner = match.group(1).strip()
    if not partner:
        # dealname form: "Last try — Moon Rocks" or "Last try - Moon Rocks"
        name = str(row.get("dealname") or "")
        for sep in (" — ", " - ", "–"):
            if sep in name:
                partner = name.split(sep, 1)[1].strip()
                break

    stage = str(row.get("dealstage") or "").strip()
    pipeline = str(row.get("pipeline") or "").strip()
    state = stage
    if pipeline and pipeline.lower() not in ("default", "default pipeline"):
        state = f"{stage} · {pipeline}" if stage else pipeline
    elif stage:
        state = stage.replace("appointmentscheduled", "appointment scheduled")

    created = _fmt_hs_date(row.get("createdate"))
    closed = _fmt_hs_date(row.get("closedate"))
    date_order = created or closed or ""

    note = description
    if len(note) > 120:
        note = note[:117] + "..."

    return {
        "id": row.get("id"),
        "name": row.get("dealname") or f"#{row.get('id')}",
        "partner_name": partner or "—",
        "amount_total": row.get("amount"),
        "state": state or "—",
        "date_order": date_order or "—",
        "closedate": closed or "",
        "pipeline": pipeline,
        "dealstage": stage,
        "note": note,
        "createdate": created,
        "_sort": str(row.get("createdate") or row.get("hs_lastmodifieddate") or ""),
    }


def _fmt_hs_date(value) -> str:
    """HubSpot often returns epoch ms as string; also accepts ISO."""
    if value in (None, ""):
        return ""
    text = str(value).strip()
    if text.isdigit():
        try:
            ms = int(text)
            if ms > 10_000_000_000:  # ms vs seconds
                ms = ms / 1000.0
            return datetime.utcfromtimestamp(ms).strftime("%Y-%m-%d %H:%M")
        except (OSError, OverflowError, ValueError):
            return text[:19]
    if "T" in text:
        return text.replace("T", " ")[:16]
    return text[:19]


def _limit_from(request, instruction_row) -> int:
    limit = 50
    try:
        mq = getattr(request, "mq_message_data", None) if request is not None else None
        if isinstance(mq, dict) and mq.get("limit") not in (None, ""):
            limit = int(mq.get("limit"))
        elif instruction_row and isinstance(
            getattr(instruction_row, "parameters_json", None), dict
        ):
            limit = int(instruction_row.parameters_json.get("limit") or 50)
    except (TypeError, ValueError):
        limit = 50
    return max(1, min(limit, 200))


def _force_save_callback(request, instruction_row, payload):
    tenant = getattr(request, "tenant", None)
    if tenant is None:
        try:
            from dose.utils import get_current_tenant

            tenant = get_current_tenant(request)
        except Exception:
            tenant = None
    if not tenant or not getattr(tenant, "schema_name", None):
        logger.warning("[HubSpotListSales] CallBackData skipped — no tenant")
        return None
    try:
        from dose.models import CallBackData
        from dose.passthrough.orchestration_log import ensure_tenant_search_path

        if not ensure_tenant_search_path(tenant, "hubspot_list_sales"):
            return None
        return CallBackData.objects.create(
            tenant=tenant,
            matchingEventKey=(
                getattr(instruction_row, "eventKey", None) or "hubspot.list_sales"
            ),
            description="HubSpot sales/deals list (bookmark capture)",
            parameters_json=payload,
            callbackdata=payload,
        )
    except Exception as exc:
        logger.error("[HubSpotListSales] CallBackData save failed: %s", exc)
        return None
