"""Fetch HubSpot contacts into CallBackData (endpoint-home bookmark)."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from __future__ import annotations

import logging

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import service_result
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.hubspot_api import HubspotApiError, HubspotApiService, HubspotNotConnected

logger = logging.getLogger(__name__)


class HubSpotListContacts(AtomicServiceBase):
    atomic_apps = ("hubspot",)
    atomic_category = "read"

    @staticmethod
    def get_parameters(parameters, key="HubSpotListContacts"):
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
            raw = api.list_contacts(limit=limit)
        except HubspotNotConnected as exc:
            return service_result(
                "HubSpotListContacts",
                status="error",
                error="not_connected",
                detail=str(exc),
                hubspot=hubspot_meta,
            )
        except HubspotApiError as exc:
            logger.error("[HubSpotListContacts] %s", exc)
            return service_result(
                "HubSpotListContacts",
                status="error",
                error="api_error",
                detail=str(exc),
                hubspot=hubspot_meta,
            )
        except Exception as exc:
            logger.error("[HubSpotListContacts] unexpected: %s", exc)
            return service_result(
                "HubSpotListContacts",
                status="error",
                error="error",
                detail=str(exc),
                hubspot=hubspot_meta,
            )

        contacts = []
        for row in raw or []:
            first = row.get("firstname") or ""
            last = row.get("lastname") or ""
            name = f"{first} {last}".strip() or (row.get("email") or f"#{row.get('id')}")
            contacts.append(
                {
                    "id": row.get("id"),
                    "name": name,
                    "email": row.get("email") or "",
                    "phone": row.get("phone") or "",
                    "parent_name": row.get("company") or "",
                }
            )

        result = service_result(
            "HubSpotListContacts",
            status="success",
            count=len(contacts),
            contacts=contacts,
            hubspot=hubspot_meta,
        )
        callback_row = _force_save_callback(request, instruction_row, result)
        if callback_row is not None:
            result["callback_id"] = getattr(callback_row, "id", None)
            result["callback_description"] = getattr(
                callback_row, "description", None
            ) or "HubSpot contact list (bookmark capture)"
            result["matching_event_key"] = getattr(
                callback_row, "matchingEventKey", None
            ) or "hubspot.list_contacts"
        return result


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
        logger.warning("[HubSpotListContacts] CallBackData skipped — no tenant")
        return None
    try:
        from dose.models import CallBackData
        from dose.passthrough.orchestration_log import ensure_tenant_search_path

        if not ensure_tenant_search_path(tenant, "hubspot_list_contacts"):
            return None
        return CallBackData.objects.create(
            tenant=tenant,
            matchingEventKey=(
                getattr(instruction_row, "eventKey", None) or "hubspot.list_contacts"
            ),
            description="HubSpot contact list (bookmark capture)",
            parameters_json=payload,
            callbackdata=payload,
        )
    except Exception as exc:
        logger.error("[HubSpotListContacts] CallBackData save failed: %s", exc)
        return None
