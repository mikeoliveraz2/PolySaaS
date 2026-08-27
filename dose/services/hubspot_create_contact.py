"""Create a HubSpot CRM contact from a Slack wireframe contact payload.

Paired to slack.webhook.contact alongside OdooCreatePartner.
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
from __future__ import annotations

import json
import logging

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import maybe_save_callback, service_result
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.hubspot_api import HubspotApiError, HubspotApiService, HubspotNotConnected

logger = logging.getLogger(__name__)

_DEMO_COMPANY = "Big Guys Warehouse"


class HubSpotCreateContact(AtomicServiceBase):
    atomic_apps = ("hubspot",)
    atomic_category = "write"

    @staticmethod
    def get_parameters(parameters, key="HubSpotCreateContact"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        payload = _extract_contact_payload(request)
        name = str(payload.get("name") or "").strip()
        if not name:
            result = service_result(
                "HubSpotCreateContact",
                status="error",
                error="missing_name",
            )
            maybe_save_callback(
                request,
                instruction_row,
                result,
                description="HubSpotCreateContact missing name",
            )
            return result

        firstname, lastname = _split_name(name)
        props = {
            "firstname": firstname,
            "lastname": lastname,
            "email": str(payload.get("email") or "").strip(),
            "phone": str(payload.get("phone") or "").strip(),
            "company": str(payload.get("company") or _DEMO_COMPANY).strip()
            or _DEMO_COMPANY,
        }

        tenant = getattr(request, "tenant", None)
        try:
            api = HubspotApiService.for_tenant(tenant)
            created = api.create_contact(props)
        except HubspotNotConnected as exc:
            result = service_result(
                "HubSpotCreateContact",
                status="error",
                error="not_connected",
                detail=str(exc),
            )
            maybe_save_callback(
                request,
                instruction_row,
                result,
                description="HubSpotCreateContact not connected",
            )
            return result
        except HubspotApiError as exc:
            logger.error("[HubSpotCreateContact] %s", exc)
            result = service_result(
                "HubSpotCreateContact",
                status="error",
                error="api_error",
                detail=str(exc),
            )
            maybe_save_callback(
                request,
                instruction_row,
                result,
                description="HubSpotCreateContact API error",
            )
            return result
        except Exception as exc:
            logger.error("[HubSpotCreateContact] unexpected: %s", exc)
            result = service_result(
                "HubSpotCreateContact",
                status="error",
                error="error",
                detail=str(exc),
            )
            maybe_save_callback(
                request,
                instruction_row,
                result,
                description="HubSpotCreateContact error",
            )
            return result

        contact_id = created.get("id")
        result = service_result(
            "HubSpotCreateContact",
            status="success",
            contact_id=contact_id,
            email=props.get("email") or "",
            name=name,
            company=props.get("company") or "",
            created=True,
        )
        maybe_save_callback(
            request,
            instruction_row,
            result,
            description=f"HubSpot contact created: {name}",
        )
        return result


def _split_name(name: str) -> tuple[str, str]:
    parts = name.split(None, 1)
    if len(parts) == 1:
        return parts[0], parts[0]
    return parts[0], parts[1]


def _extract_contact_payload(request) -> dict:
    data = getattr(request, "mq_message_data", None) if request is not None else None
    if isinstance(data, dict) and data:
        nested = data.get("normalized_data")
        return dict(nested) if isinstance(nested, dict) else dict(data)
    body = getattr(request, "body", None) if request is not None else None
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    if isinstance(body, str) and body.strip():
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            nested = parsed.get("normalized_data")
            return dict(nested) if isinstance(nested, dict) else parsed
    return {}
