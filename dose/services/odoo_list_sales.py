"""Fetch current Odoo sales orders/quotations into CallBackData for analysis.

Endpoint-home bookmark: Sales (direct_event odoo.list_sales).
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from __future__ import annotations

import logging

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import service_result
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.odoo_rpc import (
    OdooRpcClient,
    OdooRpcError,
    load_odoo_rpc_config,
    public_config,
)

logger = logging.getLogger(__name__)

_SALE_FIELDS = (
    "id",
    "name",
    "partner_id",
    "amount_total",
    "state",
    "date_order",
)


class OdooListSales(AtomicServiceBase):
    atomic_apps = ("odoo",)
    atomic_category = "read"

    @staticmethod
    def get_parameters(parameters, key="OdooListSales"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row=None):
        config = load_odoo_rpc_config(request=request, instruction_row=instruction_row)
        pub = public_config(config)
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
        limit = max(1, min(limit, 200))

        try:
            client = OdooRpcClient.from_config(config)
            client.authenticate()
            rows = client.execute_kw(
                "sale.order",
                "search_read",
                [[]],
                {
                    "fields": list(_SALE_FIELDS),
                    "limit": limit,
                    "order": "date_order desc, id desc",
                },
            )
        except OdooRpcError as exc:
            logger.error("[OdooListSales] %s: %s", exc.status, exc)
            return service_result(
                "OdooListSales",
                status="error",
                error=exc.status,
                detail=str(exc),
                odoo=pub,
            )
        except Exception as exc:
            logger.error("[OdooListSales] unexpected: %s", exc)
            return service_result(
                "OdooListSales",
                status="error",
                error="error",
                detail=str(exc),
                odoo=pub,
            )

        sales = []
        for row in rows or []:
            partner = row.get("partner_id")
            if isinstance(partner, (list, tuple)) and partner:
                partner_name = partner[1] if len(partner) > 1 else str(partner[0])
                partner_id = partner[0]
            else:
                partner_name = partner or ""
                partner_id = None
            sales.append(
                {
                    "id": row.get("id"),
                    "name": row.get("name") or "",
                    "partner_id": partner_id,
                    "partner_name": partner_name,
                    "amount_total": row.get("amount_total"),
                    "state": row.get("state") or "",
                    "date_order": row.get("date_order") or "",
                }
            )

        result = service_result(
            "OdooListSales",
            status="success",
            count=len(sales),
            sales=sales,
            odoo=pub,
        )
        callback_row = _force_save_callback(request, instruction_row, result)
        if callback_row is not None:
            result["callback_id"] = getattr(callback_row, "id", None)
            result["callback_description"] = getattr(
                callback_row, "description", None
            ) or "Odoo sales order list (bookmark capture)"
            result["matching_event_key"] = getattr(
                callback_row, "matchingEventKey", None
            ) or "odoo.list_sales"
        return result


def _force_save_callback(request, instruction_row, payload):
    """Always persist sales list for analysis (bookmark intent)."""
    tenant = getattr(request, "tenant", None)
    if tenant is None:
        try:
            from dose.utils import get_current_tenant

            tenant = get_current_tenant(request)
        except Exception:
            tenant = None
    if not tenant or not getattr(tenant, "schema_name", None):
        logger.warning("[OdooListSales] CallBackData skipped — no tenant")
        return None
    try:
        from dose.models import CallBackData
        from dose.passthrough.orchestration_log import ensure_tenant_search_path

        if not ensure_tenant_search_path(tenant, "odoo_list_sales"):
            return None
        return CallBackData.objects.create(
            tenant=tenant,
            matchingEventKey=(
                getattr(instruction_row, "eventKey", None) or "odoo.list_sales"
            ),
            description="Odoo sales order list (bookmark capture)",
            parameters_json=payload,
            callbackdata=payload,
        )
    except Exception as exc:
        logger.error("[OdooListSales] CallBackData save failed: %s", exc)
        return None
