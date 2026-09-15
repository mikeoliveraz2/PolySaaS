# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Founders Beta $10 + Mattermost CP — 2026-09-16
# Mattermost endpoint-home actions — Control Panel New contact / New sale
# Owner-approved 2026-09-14: mirror Slack popup forms → same Odoo mailbox path.
import uuid

from django.utils import timezone

from dose.webhook_events import publish_slack_wireframe_event

from .base import EndpointAction, EndpointActionAdapter


def _payload(kind: str, supplied: dict) -> dict:
    allowed = (
        {
            "name": 120,
            "email": 120,
            "phone": 40,
            "street": 120,
            "city": 80,
            "zip": 20,
            "is_company": 8,
        }
        if kind == "contact"
        else {
            "partner_name": 120,
            "partner_email": 120,
            "order_reference": 80,
            "amount": 24,
            "deal_stage": 40,
            "note": 400,
        }
    )
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
    required = "name" if kind == "contact" else "partner_name"
    if supplied and not cleaned[required]:
        raise ValueError(f"{required} is required")

    token = uuid.uuid4().hex[:10]
    stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    if kind == "contact":
        payload = {
            "demo_id": token,
            "name": cleaned["name"] or f"Mattermost Contact {stamp}",
            "email": cleaned["email"] or f"mm.contact.{token}@example.com",
            "phone": cleaned["phone"] or "+1 555 0100",
            "is_company": cleaned["is_company"].lower() in ("1", "true", "yes", "company"),
        }
        for field in ("street", "city", "zip"):
            if cleaned[field]:
                payload[field] = cleaned[field]
        return payload
    return {
        "demo_id": token,
        "partner_name": cleaned["partner_name"] or f"Mattermost Buyer {stamp}",
        "partner_email": cleaned["partner_email"]
        or f"mm.buyer.{token}@example.com",
        "order_reference": cleaned["order_reference"]
        or f"MM-{stamp}-{token[:4]}",
        "amount": cleaned["amount"],
        "deal_stage": cleaned["deal_stage"] or "appointmentscheduled",
        "note": cleaned["note"]
        or "Draft quotation created from the PolySaaS Mattermost endpoint home.",
    }


class MattermostEndpointActionAdapter(EndpointActionAdapter):
    # Match Slack Control Panel: bookmarks for New contact / New sale + popup forms.
    # Never embed the Slack wireframe mock (purple sidebar) on Mattermost home.
    surface_template = ""
    browse_mode = "passthrough"
    default_bookmarks = (
        {
            "key": "new-contact",
            "title": "New contact",
            "destination_type": "popup_form",
            "target": "mattermost.contact",
            "icon": "contact",
        },
        {
            "key": "new-sale",
            "title": "New sale",
            "destination_type": "popup_form",
            "target": "mattermost.sale",
            "icon": "sale",
        },
    )

    @classmethod
    def matches_endpoint(cls, endpoint) -> bool:
        slug = (getattr(endpoint, "slug", "") or "").strip().lower()
        url = (getattr(endpoint, "endpoint_url", "") or "").lower()
        host = ""
        try:
            from urllib.parse import urlparse

            host = (urlparse(getattr(endpoint, "endpoint_url", "") or "").hostname or "").lower()
        except Exception:
            host = ""
        return (
            slug == "mattermost"
            or "mattermost" in url
            or host == "mattermost"
            or ":8065" in url
            or slug.endswith(":8065")
            or slug.startswith("mm.")
        )

    def actions(self):
        return {
            "mattermost.contact": EndpointAction(
                key="mattermost.contact",
                kind="popup_form",
                title="New contact",
                build_payload=lambda supplied: _payload("contact", supplied),
                publish=lambda tenant, payload: publish_slack_wireframe_event(
                    tenant, "contact", payload
                ),
            ),
            "mattermost.sale": EndpointAction(
                key="mattermost.sale",
                kind="popup_form",
                title="New sale",
                build_payload=lambda supplied: _payload("sale", supplied),
                publish=lambda tenant, payload: publish_slack_wireframe_event(
                    tenant, "sale", payload
                ),
            ),
        }
