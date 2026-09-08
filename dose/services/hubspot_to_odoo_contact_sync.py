# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: HubSpot → Odoo Contact Creation — 2026-09-08

"""
HubSpotToOdooContactSync — receives HubSpot contact webhooks and publishes onto
the same contact mailbox/topic as Slack and Mattermost
(`slack.message.contact` → OdooCreatePartner).

Does not invent a second Odoo write path. After extracting HubSpot properties,
it calls publish_slack_contact_event() so the existing Slack → Odoo instruction
runs.

Triggered by: POST /dose/webhook/hubspot/<tenant_slug>/
              (generic_inbound_webhook → this AtomicService)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.webhook_events import publish_slack_contact_event

logger = logging.getLogger(__name__)


class HubSpotToOdooContactSync(AtomicServiceBase):
    """
    HubSpot contact webhook → same mailbox as Slack/Mattermost contact producers.
    Idempotent downstream via OdooCreatePartner (find-or-create by email).
    """
    atomic_apps = ("hubspot", "odoo")
    atomic_category = "integration"

    @staticmethod
    def get_parameters(parameters):
        return filter_parameters_for_service(parameters, "HubSpotToOdooContactSync")

    @staticmethod
    def execute_and_save(request, instruction_row):
        timestamp = datetime.now().isoformat()

        contact_props = HubSpotToOdooContactSync._extract_contact_props(request)
        if not contact_props:
            logger.warning("[HS→mailbox] No contact properties in request body — skipping")
            return {"status": "skipped", "reason": "no_contact_properties"}

        name = (contact_props.get("name") or "").strip()
        email = (contact_props.get("email") or "").strip()
        company = (contact_props.get("company") or "").strip() or "HubSpot"

        # FlowLink sometimes posts unexpanded {{tokens}} — reject those.
        if "{{" in name or "{{" in email or "{{" in company:
            logger.warning("[HS→mailbox] Unexpanded template tokens in payload — skipping")
            return {"status": "skipped", "reason": "unexpanded_tokens", "props": contact_props}

        if not name:
            logger.warning("[HS→mailbox] Contact has no usable name — skipping")
            return {"status": "skipped", "reason": "missing_name", "props": contact_props}
        if not email:
            logger.warning("[HS→mailbox] Contact has no email — skipping")
            return {"status": "skipped", "reason": "missing_email", "props": contact_props}

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return {"status": "error", "error": "missing_tenant"}

        contact_data = {
            "name": name[:100],
            "email": email[:100],
            "company": company[:100],
            "slack_user_id": "",
            "slack_channel_id": "hubspot",
            "slack_message_ts": timestamp,
            "slack_team_id": getattr(tenant, "slug", "") or getattr(tenant, "schema_name", ""),
        }

        result = publish_slack_contact_event(tenant, contact_data)
        if result.get("success"):
            logger.info(
                "[HS→mailbox] queued contact name=%s email=%s event_id=%s",
                name, email, result.get("event_id"),
            )
            return {
                "status": "queued",
                "service_name": "HubSpotToOdooContactSync",
                "execution_timestamp": timestamp,
                "source_app": "hubspot",
                "entity": "contact",
                "action": "queued",
                "event_id": result.get("event_id"),
                "mailbox_id": result.get("mailbox_id"),
                "topic": "slack.message.contact",
                "contact": {"name": name, "email": email, "company": company},
            }

        return {
            "status": "error",
            "service_name": "HubSpotToOdooContactSync",
            "error": result.get("error", "Failed to queue event"),
        }

    @staticmethod
    def _extract_contact_props(request) -> dict:
        """
        Extract contact properties from a request body.

        Shape 1 — v3 flat: {"properties": {"email": "...", "firstname": "...", ...}}
        Shape 2 — v3 nested: {"properties": {"email": {"value": "..."}, ...}}
        Shape 3 — v1 list: {"properties": [{"property": "email", "value": "..."}, ...]}
        Shape 4 — flat root: {"email": "...", "firstname": "...", ...}
        Shape 5 — CRM event array: [{"subscriptionType": "contact.creation", ...}]
                  (no properties — returns {} unless workflow embeds props)
        """
        try:
            body_bytes = getattr(request, "body", None) or b""
            if isinstance(body_bytes, str):
                body_bytes = body_bytes.encode("utf-8")
            data = json.loads(body_bytes.decode("utf-8", errors="replace") or "{}")
        except Exception:
            data = {}

        if isinstance(data, list):
            data = data[0] if data else {}

        raw_props = data.get("properties")

        if isinstance(raw_props, list):
            props: dict = {}
            for item in raw_props:
                key = item.get("property", "")
                val = item.get("value", "")
                if key == "email":
                    props["email"] = val
                elif key == "firstname":
                    props.setdefault("_firstname", val)
                elif key == "lastname":
                    props.setdefault("_lastname", val)
                elif key == "phone":
                    props["phone"] = val
                elif key == "company":
                    props["company"] = val
            fn = props.pop("_firstname", "")
            ln = props.pop("_lastname", "")
            props["name"] = f"{fn} {ln}".strip()
            if not props.get("email") and not props.get("name"):
                return {}
            return props

        if isinstance(raw_props, dict):
            def _val(v):
                return v["value"] if isinstance(v, dict) and "value" in v else v

            raw = {k: _val(v) for k, v in raw_props.items()}
        elif any(k in data for k in ("email", "firstname", "lastname", "phone")):
            raw = data
        else:
            return {}

        props = {
            "email": raw.get("email", ""),
            "phone": raw.get("phone", raw.get("mobilephone", "")),
            "company": raw.get("company", ""),
            "jobtitle": raw.get("jobtitle", ""),
            "website": raw.get("website", ""),
            "address": raw.get("address", ""),
            "city": raw.get("city", ""),
            "zip": raw.get("zip", ""),
            "country": raw.get("country", ""),
        }
        firstname = raw.get("firstname", "")
        lastname = raw.get("lastname", "")
        props["name"] = f"{firstname} {lastname}".strip() or raw.get("name", "")

        if not props.get("email") and not props.get("name"):
            return {}
        return props
