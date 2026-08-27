"""Odoo endpoint-home actions and default bookmarks."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from __future__ import annotations

from types import SimpleNamespace

from dose.endpoint_browser import endpoint_app_logo_key
from dose.passthrough.orchestration_log import ensure_tenant_search_path

from .base import EndpointAction, EndpointActionAdapter


def _list_limit_payload(supplied: dict) -> dict:
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


def _list_invoices_payload(supplied: dict) -> dict:
    return _list_limit_payload(supplied)


def _list_contacts_payload(supplied: dict) -> dict:
    return _list_limit_payload(supplied)


def _list_sales_payload(supplied: dict) -> dict:
    return _list_limit_payload(supplied)


def _publish_list_invoices(tenant, payload: dict) -> dict:
    """Run OdooListInvoices sync and persist CallBackData for analysis."""
    from dose.services.odoo_list_invoices import OdooListInvoices

    if not tenant or not getattr(tenant, "schema_name", None):
        return {"success": False, "error": "no tenant"}
    if not ensure_tenant_search_path(tenant, "odoo_list_invoices_action"):
        return {"success": False, "error": "invalid tenant schema"}

    request = SimpleNamespace(
        tenant=tenant,
        mq_message_data=dict(payload or {}),
        body=b"{}",
        atomic_parameters=[],
        user=None,
    )
    result = OdooListInvoices.execute_and_save(request, None)
    ok = result.get("status") == "success"
    count = int(result.get("count") or 0)
    invoices = result.get("invoices") if isinstance(result.get("invoices"), list) else []
    if ok:
        detail = f"{count} invoice{'s' if count != 1 else ''} saved to CallBackData"
    else:
        detail = (
            result.get("detail")
            or result.get("error")
            or "Could not list Odoo invoices"
        )
    odoo_pub = result.get("odoo") if isinstance(result.get("odoo"), dict) else {}
    return {
        "success": ok,
        "sync": True,
        "status": result.get("status"),
        "count": count,
        "detail": detail,
        "action_path": "odoo.list_invoices",
        "list_kind": "invoices",
        "error": None if ok else detail,
        "callback_id": result.get("callback_id"),
        "callback_description": result.get("callback_description")
        or "Odoo customer invoice list (bookmark capture)",
        "matching_event_key": result.get("matching_event_key") or "odoo.list_invoices",
        "odoo": odoo_pub,
        "invoices": invoices,
        "popup": "callback_record",
    }


def _publish_list_contacts(tenant, payload: dict) -> dict:
    """Run OdooListContacts sync and persist CallBackData for analysis."""
    from dose.services.odoo_list_contacts import OdooListContacts

    if not tenant or not getattr(tenant, "schema_name", None):
        return {"success": False, "error": "no tenant"}
    if not ensure_tenant_search_path(tenant, "odoo_list_contacts_action"):
        return {"success": False, "error": "invalid tenant schema"}

    request = SimpleNamespace(
        tenant=tenant,
        mq_message_data=dict(payload or {}),
        body=b"{}",
        atomic_parameters=[],
        user=None,
    )
    result = OdooListContacts.execute_and_save(request, None)
    ok = result.get("status") == "success"
    count = int(result.get("count") or 0)
    contacts = result.get("contacts") if isinstance(result.get("contacts"), list) else []
    if ok:
        detail = f"{count} contact{'s' if count != 1 else ''} saved to CallBackData"
    else:
        detail = (
            result.get("detail")
            or result.get("error")
            or "Could not list Odoo contacts"
        )
    odoo_pub = result.get("odoo") if isinstance(result.get("odoo"), dict) else {}
    return {
        "success": ok,
        "sync": True,
        "status": result.get("status"),
        "count": count,
        "detail": detail,
        "action_path": "odoo.list_contacts",
        "list_kind": "contacts",
        "error": None if ok else detail,
        "callback_id": result.get("callback_id"),
        "callback_description": result.get("callback_description")
        or "Odoo customer contact list (bookmark capture)",
        "matching_event_key": result.get("matching_event_key") or "odoo.list_contacts",
        "odoo": odoo_pub,
        "contacts": contacts,
        "popup": "callback_record",
    }


def _publish_list_sales(tenant, payload: dict) -> dict:
    """Run OdooListSales sync and persist CallBackData for analysis."""
    from dose.services.odoo_list_sales import OdooListSales

    if not tenant or not getattr(tenant, "schema_name", None):
        return {"success": False, "error": "no tenant"}
    if not ensure_tenant_search_path(tenant, "odoo_list_sales_action"):
        return {"success": False, "error": "invalid tenant schema"}

    request = SimpleNamespace(
        tenant=tenant,
        mq_message_data=dict(payload or {}),
        body=b"{}",
        atomic_parameters=[],
        user=None,
    )
    result = OdooListSales.execute_and_save(request, None)
    ok = result.get("status") == "success"
    count = int(result.get("count") or 0)
    sales = result.get("sales") if isinstance(result.get("sales"), list) else []
    if ok:
        detail = f"{count} sale{'s' if count != 1 else ''} saved to CallBackData"
    else:
        detail = (
            result.get("detail")
            or result.get("error")
            or "Could not list Odoo sales"
        )
    odoo_pub = result.get("odoo") if isinstance(result.get("odoo"), dict) else {}
    return {
        "success": ok,
        "sync": True,
        "status": result.get("status"),
        "count": count,
        "detail": detail,
        "action_path": "odoo.list_sales",
        "list_kind": "sales",
        "error": None if ok else detail,
        "callback_id": result.get("callback_id"),
        "callback_description": result.get("callback_description")
        or "Odoo sales order list (bookmark capture)",
        "matching_event_key": result.get("matching_event_key") or "odoo.list_sales",
        "odoo": odoo_pub,
        "sales": sales,
        "popup": "callback_record",
    }


class OdooEndpointActionAdapter(EndpointActionAdapter):
    browse_mode = "passthrough"
    default_bookmarks = (
        {
            "key": "contacts",
            "title": "Contacts",
            "destination_type": "direct_event",
            "target": "odoo.list_contacts",
            "icon": "ctc",
            "description": "Fetch current customer contacts into CallBackData",
        },
        {
            "key": "sales",
            "title": "Sales",
            "destination_type": "direct_event",
            "target": "odoo.list_sales",
            "icon": "sal",
            "description": "Fetch current sales orders into CallBackData",
        },
        {
            "key": "invoices",
            "title": "Invoices",
            "destination_type": "direct_event",
            "target": "odoo.list_invoices",
            "icon": "inv",
            "description": "Fetch current customer invoices into CallBackData",
        },
    )

    @classmethod
    def matches_endpoint(cls, endpoint) -> bool:
        return endpoint_app_logo_key(endpoint) == "odoo"

    def actions(self):
        return {
            "odoo.list_contacts": EndpointAction(
                key="odoo.list_contacts",
                kind="direct_event",
                title="Contacts",
                build_payload=_list_contacts_payload,
                publish=_publish_list_contacts,
            ),
            "odoo.list_sales": EndpointAction(
                key="odoo.list_sales",
                kind="direct_event",
                title="Sales",
                build_payload=_list_sales_payload,
                publish=_publish_list_sales,
            ),
            "odoo.list_invoices": EndpointAction(
                key="odoo.list_invoices",
                kind="direct_event",
                title="Invoices",
                build_payload=_list_invoices_payload,
                publish=_publish_list_invoices,
            ),
        }
