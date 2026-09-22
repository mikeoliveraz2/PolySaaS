"""Odoo endpoint-home actions and default bookmarks."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
# FIX 2026-09-01 (owner-approved): three copied publishers replaced by shared ListSpec.
# BINGO: Geronimo Chat Integration — 2026-09-02
# Owner-approved 2026-09-21: Capture contacts → Captured Topics.
# Owner-approved 2026-09-22: New contact popup → OdooCreatePartner orch.
# Owner-approved 2026-09-22: one Contacts bookmark (shared topic); drop CallBackData duplicate.
from __future__ import annotations

import uuid

from django.utils import timezone

from dose.endpoint_browser import endpoint_app_logo_key
from dose.passthrough.orchestration_log import ensure_tenant_search_path
from dose.webhook_events import publish_odoo_cp_contact_event

from .base import EndpointAction, EndpointActionAdapter
from .contact_capture_publish import publish_odoo_capture_contacts
from .list_publisher import ListSpec, list_limit_payload, make_publisher


def _guard(tenant, label):
    """Resolved from this module's globals so tests can patch it here."""
    return ensure_tenant_search_path(tenant, label)


def _new_contact_payload(supplied: dict) -> dict:
    """Same fields as Slack/Mattermost contact popup → OdooCreatePartner."""
    allowed = {
        "name": 120,
        "email": 120,
        "phone": 40,
        "street": 120,
        "city": 80,
        "zip": 20,
        "is_company": 8,
    }
    unknown = set(supplied) - set(allowed)
    if unknown:
        raise ValueError("Unsupported field(s): " + ", ".join(sorted(unknown)))
    cleaned = {}
    for field, maximum in allowed.items():
        value = supplied.get(field, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise ValueError(f"{field} must be text")
        cleaned[field] = value.strip()[:maximum]
    if supplied and not cleaned["name"]:
        raise ValueError("name is required")

    token = uuid.uuid4().hex[:10]
    stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    payload = {
        "demo_id": token,
        "name": cleaned["name"] or f"Odoo Contact {stamp}",
        "email": cleaned["email"] or f"odoo.contact.{token}@example.com",
        "phone": cleaned["phone"] or "+1 555 0100",
        "is_company": cleaned["is_company"].lower()
        in ("1", "true", "yes", "company"),
    }
    for field in ("street", "city", "zip"):
        if cleaned[field]:
            payload[field] = cleaned[field]
    return payload


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
            "key": "new-contact",
            "title": "New contact",
            "destination_type": "popup_form",
            "target": "odoo.contact",
            "icon": "contact",
            "description": "Add one contact → OdooCreatePartner orchestration",
        },
        {
            "key": "contacts",
            "title": "Contacts",
            "destination_type": "direct_event",
            "target": "odoo.capture_contacts",
            "icon": "ctc",
            "description": "GET contacts into the shared Captured Topics Contacts queue",
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

    def chat_prompts(self) -> list:
        """Geronimo chat preset prompts for Odoo endpoints."""
        from dose.ai_prompts.prompt_library import get_prompts_for_endpoint

        # Return prompts for the current data panel (if any).
        # For simplicity, return invoices prompts as default.
        # In a more sophisticated implementation, this could be context-aware
        # based on which panel is currently being viewed.
        return get_prompts_for_endpoint("odoo.invoices")

    def chat_context_hint(self) -> str:
        """Context hint for LLM about Odoo invoice data."""
        from dose.ai_prompts.prompt_library import get_context_hint_for_endpoint

        return get_context_hint_for_endpoint("odoo.invoices")

    def actions(self):
        return {
            "odoo.contact": EndpointAction(
                key="odoo.contact",
                kind="popup_form",
                title="New contact",
                build_payload=_new_contact_payload,
                publish=publish_odoo_cp_contact_event,
            ),
            "odoo.capture_contacts": EndpointAction(
                key="odoo.capture_contacts",
                kind="direct_event",
                title="Contacts",
                build_payload=list_limit_payload,
                publish=publish_odoo_capture_contacts,
            ),
            # Kept for older Instruction / CallBackData bindings; not a default bookmark.
            "odoo.list_contacts": EndpointAction(
                key="odoo.list_contacts",
                kind="direct_event",
                title="Contacts (CallBackData)",
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
