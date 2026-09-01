"""Odoo endpoint-home actions and default bookmarks."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
# FIX 2026-09-01 (owner-approved): three copied publishers replaced by shared ListSpec.
from __future__ import annotations

from dose.endpoint_browser import endpoint_app_logo_key
from dose.passthrough.orchestration_log import ensure_tenant_search_path

from .base import EndpointAction, EndpointActionAdapter
from .list_publisher import ListSpec, list_limit_payload, make_publisher


def _guard(tenant, label):
    """Resolved from this module's globals so tests can patch it here."""
    return ensure_tenant_search_path(tenant, label)


def _load_list_invoices():
    from dose.services.odoo_list_invoices import OdooListInvoices

    return OdooListInvoices


def _load_list_contacts():
    from dose.services.odoo_list_contacts import OdooListContacts

    return OdooListContacts


def _load_list_sales():
    from dose.services.odoo_list_sales import OdooListSales

    return OdooListSales


LIST_INVOICES = ListSpec(
    action_path="odoo.list_invoices",
    object_type="invoice",
    vendor_key="odoo",
    search_path_label="odoo_list_invoices_action",
    callback_description="Odoo customer invoice list (bookmark capture)",
    error_message="Could not list Odoo invoices",
    load_service=_load_list_invoices,
    guard=_guard,
)

LIST_CONTACTS = ListSpec(
    action_path="odoo.list_contacts",
    object_type="contact",
    vendor_key="odoo",
    search_path_label="odoo_list_contacts_action",
    callback_description="Odoo customer contact list (bookmark capture)",
    error_message="Could not list Odoo contacts",
    load_service=_load_list_contacts,
    guard=_guard,
)

LIST_SALES = ListSpec(
    action_path="odoo.list_sales",
    object_type="sale",
    vendor_key="odoo",
    search_path_label="odoo_list_sales_action",
    callback_description="Odoo sales order list (bookmark capture)",
    error_message="Could not list Odoo sales",
    load_service=_load_list_sales,
    guard=_guard,
)

# Deprecated: the pre-refactor private names, kept so existing callers and
# tests keep working for one release.
_list_limit_payload = list_limit_payload
_list_invoices_payload = list_limit_payload
_list_contacts_payload = list_limit_payload
_list_sales_payload = list_limit_payload
_publish_list_invoices = make_publisher(LIST_INVOICES)
_publish_list_contacts = make_publisher(LIST_CONTACTS)
_publish_list_sales = make_publisher(LIST_SALES)


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
                build_payload=list_limit_payload,
                publish=make_publisher(LIST_CONTACTS),
            ),
            "odoo.list_sales": EndpointAction(
                key="odoo.list_sales",
                kind="direct_event",
                title="Sales",
                build_payload=list_limit_payload,
                publish=make_publisher(LIST_SALES),
            ),
            "odoo.list_invoices": EndpointAction(
                key="odoo.list_invoices",
                kind="direct_event",
                title="Invoices",
                build_payload=list_limit_payload,
                publish=make_publisher(LIST_INVOICES),
            ),
        }
