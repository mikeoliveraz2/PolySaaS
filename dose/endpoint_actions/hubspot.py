"""HubSpot endpoint-home actions and default bookmarks."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from __future__ import annotations

from types import SimpleNamespace

from dose.endpoint_browser import endpoint_app_logo_key
from dose.passthrough.orchestration_log import ensure_tenant_search_path

from .base import EndpointAction, EndpointActionAdapter


def _list_limit_payload(supplied: dict) -> dict:
    if not isinstance(supplied, dict):
        return {}
    limit = supplied.get("limit")
    if limit in (None, ""):
        return {}
    try:
        return {"limit": max(1, min(int(limit), 200))}
    except (TypeError, ValueError):
        return {}


def _list_contacts_payload(supplied: dict) -> dict:
    return _list_limit_payload(supplied)


def _list_sales_payload(supplied: dict) -> dict:
    return _list_limit_payload(supplied)


def _publish_list_contacts(tenant, payload: dict) -> dict:
    from dose.services.hubspot_list_contacts import HubSpotListContacts

    if not tenant or not getattr(tenant, "schema_name", None):
        return {"success": False, "error": "no tenant"}
    if not ensure_tenant_search_path(tenant, "hubspot_list_contacts_action"):
        return {"success": False, "error": "invalid tenant schema"}

    request = SimpleNamespace(
        tenant=tenant,
        mq_message_data=dict(payload or {}),
        body=b"{}",
        atomic_parameters=[],
        user=None,
    )
    result = HubSpotListContacts.execute_and_save(request, None)
    ok = result.get("status") == "success"
    count = int(result.get("count") or 0)
    contacts = result.get("contacts") if isinstance(result.get("contacts"), list) else []
    if ok:
        detail = f"{count} contact{'s' if count != 1 else ''} saved to CallBackData"
    else:
        detail = (
            result.get("detail")
            or result.get("error")
            or "Could not list HubSpot contacts"
        )
    hubspot = result.get("hubspot") if isinstance(result.get("hubspot"), dict) else {}
    return {
        "success": ok,
        "sync": True,
        "status": result.get("status"),
        "count": count,
        "detail": detail,
        "action_path": "hubspot.list_contacts",
        "list_kind": "contacts",
        "error": None if ok else detail,
        "callback_id": result.get("callback_id"),
        "callback_description": result.get("callback_description")
        or "HubSpot contact list (bookmark capture)",
        "matching_event_key": result.get("matching_event_key") or "hubspot.list_contacts",
        "hubspot": hubspot,
        "contacts": contacts,
        "popup": "callback_record",
    }


def _publish_list_sales(tenant, payload: dict) -> dict:
    from dose.services.hubspot_list_sales import HubSpotListSales

    if not tenant or not getattr(tenant, "schema_name", None):
        return {"success": False, "error": "no tenant"}
    if not ensure_tenant_search_path(tenant, "hubspot_list_sales_action"):
        return {"success": False, "error": "invalid tenant schema"}

    request = SimpleNamespace(
        tenant=tenant,
        mq_message_data=dict(payload or {}),
        body=b"{}",
        atomic_parameters=[],
        user=None,
    )
    result = HubSpotListSales.execute_and_save(request, None)
    ok = result.get("status") == "success"
    count = int(result.get("count") or 0)
    sales = result.get("sales") if isinstance(result.get("sales"), list) else []
    if ok:
        detail = f"{count} sale{'s' if count != 1 else ''} saved to CallBackData"
    else:
        detail = (
            result.get("detail")
            or result.get("error")
            or "Could not list HubSpot sales"
        )
    hubspot = result.get("hubspot") if isinstance(result.get("hubspot"), dict) else {}
    return {
        "success": ok,
        "sync": True,
        "status": result.get("status"),
        "count": count,
        "detail": detail,
        "action_path": "hubspot.list_sales",
        "list_kind": "sales",
        "error": None if ok else detail,
        "callback_id": result.get("callback_id"),
        "callback_description": result.get("callback_description")
        or "HubSpot sales/deals list (bookmark capture)",
        "matching_event_key": result.get("matching_event_key") or "hubspot.list_sales",
        "hubspot": hubspot,
        "sales": sales,
        "popup": "callback_record",
    }


class HubspotEndpointActionAdapter(EndpointActionAdapter):
    browse_mode = "passthrough"
    default_bookmarks = (
        {
            "key": "contacts",
            "title": "Contacts",
            "destination_type": "direct_event",
            "target": "hubspot.list_contacts",
            "icon": "ctc",
            "description": "Fetch current HubSpot contacts into CallBackData",
        },
        {
            "key": "sales",
            "title": "Sales",
            "destination_type": "direct_event",
            "target": "hubspot.list_sales",
            "icon": "sal",
            "description": "Fetch current HubSpot deals into CallBackData",
        },
    )

    @classmethod
    def matches_endpoint(cls, endpoint) -> bool:
        return endpoint_app_logo_key(endpoint) == "hubspot"

    def actions(self):
        return {
            "hubspot.list_contacts": EndpointAction(
                key="hubspot.list_contacts",
                kind="direct_event",
                title="Contacts",
                build_payload=_list_contacts_payload,
                publish=_publish_list_contacts,
            ),
            "hubspot.list_sales": EndpointAction(
                key="hubspot.list_sales",
                kind="direct_event",
                title="Sales",
                build_payload=_list_sales_payload,
                publish=_publish_list_sales,
            ),
        }
