# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack Odoo contact/sale forms — 2026-08-25
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
# BINGO: Geronimo Chat Integration — 2026-09-02
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
            "name": cleaned["name"] or f"Slack Contact {stamp}",
            "email": cleaned["email"] or f"slack.contact.{token}@example.com",
            "phone": cleaned["phone"] or "+1 555 0100",
            "is_company": cleaned["is_company"].lower() in ("1", "true", "yes", "company"),
        }
        for field in ("street", "city", "zip"):
            if cleaned[field]:
                payload[field] = cleaned[field]
        return payload
    return {
        "demo_id": token,
        "partner_name": cleaned["partner_name"] or f"Slack Buyer {stamp}",
        "partner_email": cleaned["partner_email"]
        or f"slack.buyer.{token}@example.com",
        "order_reference": cleaned["order_reference"]
        or f"SLACK-{stamp}-{token[:4]}",
        "amount": cleaned["amount"],
        "deal_stage": cleaned["deal_stage"] or "appointmentscheduled",
        "note": cleaned["note"]
        or "Draft quotation created from the PolySaaS Slack endpoint home.",
    }


class SlackEndpointActionAdapter(EndpointActionAdapter):
    # Use unified endpoint_home.html (not custom surface_template)
    # surface_template = "polysniffer/slack_wireframe.html"  # DEPRECATED 2026-09-03
    browse_mode = "external"
    default_bookmarks = (
        {
            "key": "channel-home",
            "title": "Channel home",
            "destination_type": "mock_surface",
            "target": "slack.channel-home",
            "icon": "#",
        },
        {
            "key": "new-contact",
            "title": "New contact",
            "destination_type": "popup_form",
            "target": "slack.contact",
            "icon": "contact",
        },
        {
            "key": "new-sale",
            "title": "New sale",
            "destination_type": "popup_form",
            "target": "slack.sale",
            "icon": "sale",
        },
    )

    @classmethod
    def matches_endpoint(cls, endpoint) -> bool:
        slug = (getattr(endpoint, "slug", "") or "").strip().lower()
        url = (getattr(endpoint, "endpoint_url", "") or "").lower()
        return slug == "slack" or "slack.com" in url

    def panels(self):
        """Slack unified workspace: teams and channels as data panels."""
        from .base import EndpointPanel
        
        # Slack shows teams and channels as data exploration panels
        return (
            EndpointPanel(
                key="teams",
                title="Teams",
                object_type="team",
                action="slack.teams",
            ),
            EndpointPanel(
                key="channels",
                title="Channels",
                object_type="channel",
                action="slack.channels",
            ),
        )

    def chat_prompts(self) -> list:
        """Geronimo chat preset prompts for Slack endpoints."""
        from dose.ai_prompts.prompt_library import get_prompts_for_endpoint

        # Return prompts for Slack channels.
        return get_prompts_for_endpoint("slack.channels")

    def chat_context_hint(self) -> str:
        """Context hint for LLM about Slack channel data."""
        from dose.ai_prompts.prompt_library import get_context_hint_for_endpoint

        return get_context_hint_for_endpoint("slack.channels")

    def actions(self):
        return {
            "slack.contact": EndpointAction(
                key="slack.contact",
                kind="popup_form",
                title="New contact",
                build_payload=lambda supplied: _payload("contact", supplied),
                publish=lambda tenant, payload: publish_slack_wireframe_event(
                    tenant, "contact", payload
                ),
            ),
            "slack.sale": EndpointAction(
                key="slack.sale",
                kind="popup_form",
                title="New sale",
                build_payload=lambda supplied: _payload("sale", supplied),
                publish=lambda tenant, payload: publish_slack_wireframe_event(
                    tenant, "sale", payload
                ),
            ),
        }
