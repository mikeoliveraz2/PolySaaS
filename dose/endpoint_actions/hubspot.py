"""HubSpot endpoint-home actions and default bookmarks."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
# FIX 2026-09-01 (owner-approved): shared ListSpec publisher; Browse corrected to external.
from __future__ import annotations

from dose.endpoint_browser import endpoint_app_logo_key
from dose.passthrough.orchestration_log import ensure_tenant_search_path

from .base import EndpointAction, EndpointActionAdapter
from .list_publisher import ListSpec, list_limit_payload, make_publisher


def _guard(tenant, label):
    """Resolved from this module's globals so tests can patch it here."""
    return ensure_tenant_search_path(tenant, label)


def _load_list_contacts():
    from dose.services.hubspot_list_contacts import HubSpotListContacts

    return HubSpotListContacts


def _load_list_sales():
    from dose.services.hubspot_list_sales import HubSpotListSales

    return HubSpotListSales


LIST_CONTACTS = ListSpec(
    action_path="hubspot.list_contacts",
    object_type="contact",
    vendor_key="hubspot",
    search_path_label="hubspot_list_contacts_action",
    callback_description="HubSpot contact list (bookmark capture)",
    error_message="Could not list HubSpot contacts",
    load_service=_load_list_contacts,
    guard=_guard,
)

LIST_SALES = ListSpec(
    action_path="hubspot.list_sales",
    object_type="sale",
    vendor_key="hubspot",
    search_path_label="hubspot_list_sales_action",
    callback_description="HubSpot sales/deals list (bookmark capture)",
    error_message="Could not list HubSpot sales",
    load_service=_load_list_sales,
    guard=_guard,
)

# Deprecated: the pre-refactor private names, kept so existing callers and
# tests keep working for one release.
_list_limit_payload = list_limit_payload
_list_contacts_payload = list_limit_payload
_list_sales_payload = list_limit_payload
_publish_list_contacts = make_publisher(LIST_CONTACTS)
_publish_list_sales = make_publisher(LIST_SALES)


class HubspotEndpointActionAdapter(EndpointActionAdapter):
    # HubSpot login cannot be proxied: the SPA requires a browser-only csrf.app
    # cookie (HUBSPOT_PASSTHROUGH_STATUS_2026-06-28.md), so Browse opens the
    # real app in a top-level tab.
    browse_mode = "external"
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
                build_payload=list_limit_payload,
                publish=make_publisher(LIST_CONTACTS),
            ),
            "hubspot.list_sales": EndpointAction(
                key="hubspot.list_sales",
                kind="direct_event",
                title="Sales",
                build_payload=list_limit_payload,
                publish=make_publisher(LIST_SALES),
            ),
        }
