"""Fetch current Odoo customer contacts into CallBackData for analysis.

Endpoint-home bookmark: Contacts (direct_event odoo.list_contacts).
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

_CONTACT_FIELDS = (
    "id",
    "name",
    "email",
    "phone",
    "parent_id",
    "customer_rank",
)


class OdooListContacts(AtomicServiceBase):
    atomic_apps = ("odoo",)
    atomic_category = "read"

    @staticmethod
    def get_parameters(parameters, key="OdooListContacts"):
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
                "res.partner",
                "search_read",
                [[["customer_rank", ">", 0]]],
                {
                    "fields": list(_CONTACT_FIELDS),
                    "limit": limit,
                    "order": "name asc, id desc",
                },
            )
        except OdooRpcError as exc:
            logger.error("[OdooListContacts] %s: %s", exc.status, exc)
            return service_result(
                "OdooListContacts",
                status="error",
                error=exc.status,
                detail=str(exc),
                odoo=pub,
            )
        except Exception as exc:
            logger.error("[OdooListContacts] unexpected: %s", exc)
            return service_result(
                "OdooListContacts",
                status="error",
                error="error",
                detail=str(exc),
                odoo=pub,
            )

        contacts = []
        for row in rows or []:
            parent = row.get("parent_id")
            if isinstance(parent, (list, tuple)) and parent:
                parent_name = parent[1] if len(parent) > 1 else str(parent[0])
                parent_id = parent[0]
            else:
                parent_name = parent or ""
                parent_id = None
            contacts.append(
                {
                    "id": row.get("id"),
                    "name": row.get("name") or "",
                    "email": row.get("email") or "",
                    "phone": row.get("phone") or "",
                    "parent_id": parent_id,
                    "parent_name": parent_name,
                    "customer_rank": row.get("customer_rank"),
                }
            )

        result = service_result(
            "OdooListContacts",
            status="success",
            count=len(contacts),
            contacts=contacts,
            odoo=pub,
        )
        callback_row = _force_save_callback(request, instruction_row, result)
        if callback_row is not None:
            result["callback_id"] = getattr(callback_row, "id", None)
            result["callback_description"] = getattr(
                callback_row, "description", None
            ) or "Odoo customer contact list (bookmark capture)"
            result["matching_event_key"] = getattr(
                callback_row, "matchingEventKey", None
            ) or "odoo.list_contacts"
        return result


def _force_save_callback(request, instruction_row, payload):
    """Always persist contact list for analysis (bookmark intent)."""
    tenant = getattr(request, "tenant", None)
    if tenant is None:
        try:
            from dose.utils import get_current_tenant

            tenant = get_current_tenant(request)
        except Exception:
            tenant = None
    if not tenant or not getattr(tenant, "schema_name", None):
        logger.warning("[OdooListContacts] CallBackData skipped — no tenant")
        return None
    try:
        from dose.models import CallBackData
        from dose.passthrough.orchestration_log import ensure_tenant_search_path

        if not ensure_tenant_search_path(tenant, "odoo_list_contacts"):
            return None
        return CallBackData.objects.create(
            tenant=tenant,
            matchingEventKey=(
                getattr(instruction_row, "eventKey", None) or "odoo.list_contacts"
            ),
            description="Odoo customer contact list (bookmark capture)",
            parameters_json=payload,
            callbackdata=payload,
        )
    except Exception as exc:
        logger.error("[OdooListContacts] CallBackData save failed: %s", exc)
        return None
