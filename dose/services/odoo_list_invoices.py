"""Fetch current Odoo customer invoices into CallBackData for analysis.

Endpoint-home bookmark: Invoices (direct_event odoo.list_invoices).
"""
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

_INVOICE_FIELDS = (
    "id",
    "name",
    "partner_id",
    "amount_total",
    "amount_untaxed",
    "state",
    "move_type",
    "invoice_date",
    "payment_state",
)


class OdooListInvoices(AtomicServiceBase):
    atomic_apps = ("odoo",)
    atomic_category = "read"

    @staticmethod
    def get_parameters(parameters, key="OdooListInvoices"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row=None):
        config = load_odoo_rpc_config(request=request, instruction_row=instruction_row)
        pub = public_config(config)
        limit = 50
        try:
            if instruction_row and isinstance(
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
                "account.move",
                "search_read",
                [[["move_type", "in", ["out_invoice", "out_refund"]]]],
                {
                    "fields": list(_INVOICE_FIELDS),
                    "limit": limit,
                    "order": "invoice_date desc, id desc",
                },
            )
        except OdooRpcError as exc:
            logger.error("[OdooListInvoices] %s: %s", exc.status, exc)
            return service_result(
                "OdooListInvoices",
                status="error",
                error=exc.status,
                detail=str(exc),
                odoo=pub,
            )
        except Exception as exc:
            logger.error("[OdooListInvoices] unexpected: %s", exc)
            return service_result(
                "OdooListInvoices",
                status="error",
                error="error",
                detail=str(exc),
                odoo=pub,
            )

        invoices = []
        for row in rows or []:
            partner = row.get("partner_id")
            if isinstance(partner, (list, tuple)) and partner:
                partner_name = partner[1] if len(partner) > 1 else str(partner[0])
                partner_id = partner[0]
            else:
                partner_name = partner or ""
                partner_id = None
            invoices.append(
                {
                    "id": row.get("id"),
                    "name": row.get("name") or "",
                    "partner_id": partner_id,
                    "partner_name": partner_name,
                    "amount_total": row.get("amount_total"),
                    "amount_untaxed": row.get("amount_untaxed"),
                    "state": row.get("state") or "",
                    "move_type": row.get("move_type") or "",
                    "invoice_date": row.get("invoice_date") or "",
                    "payment_state": row.get("payment_state") or "",
                }
            )

        result = service_result(
            "OdooListInvoices",
            status="success",
            count=len(invoices),
            invoices=invoices,
            odoo=pub,
        )
        _force_save_callback(request, instruction_row, result)
        return result


def _force_save_callback(request, instruction_row, payload):
    """Always persist invoice list for analysis (bookmark intent)."""
    tenant = getattr(request, "tenant", None)
    if tenant is None:
        try:
            from dose.utils import get_current_tenant

            tenant = get_current_tenant(request)
        except Exception:
            tenant = None
    if not tenant or not getattr(tenant, "schema_name", None):
        logger.warning("[OdooListInvoices] CallBackData skipped — no tenant")
        return None
    try:
        from dose.models import CallBackData
        from dose.passthrough.orchestration_log import ensure_tenant_search_path

        if not ensure_tenant_search_path(tenant, "odoo_list_invoices"):
            return None
        return CallBackData.objects.create(
            tenant=tenant,
            matchingEventKey=(
                getattr(instruction_row, "eventKey", None) or "odoo.list_invoices"
            ),
            description="Odoo customer invoice list (bookmark capture)",
            parameters_json=payload,
            callbackdata=payload,
        )
    except Exception as exc:
        logger.error("[OdooListInvoices] CallBackData save failed: %s", exc)
        return None
