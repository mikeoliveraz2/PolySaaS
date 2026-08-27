"""Create a HubSpot CRM deal from a Slack wireframe sale payload.

Paired to slack.webhook.sale alongside OdooCreateQuotation.
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


class HubSpotCreateDeal(AtomicServiceBase):
    atomic_apps = ("hubspot",)
    atomic_category = "write"

    @staticmethod
    def get_parameters(parameters, key="HubSpotCreateDeal"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row):
        payload = _extract_sale_payload(request)
        partner_name = str(payload.get("partner_name") or "").strip()
        reference = str(payload.get("order_reference") or "").strip()
        if not partner_name or not reference:
            result = service_result(
                "HubSpotCreateDeal",
                status="error",
                error="missing_partner_or_reference",
            )
            maybe_save_callback(
                request,
                instruction_row,
                result,
                description="HubSpotCreateDeal missing partner or reference",
            )
            return result

        note = str(payload.get("note") or "").strip()
        dealname = f"{reference} — {partner_name}"
        # Always keep partner in description so list bookmarks can recover Customer.
        base_desc = f"Sale from Slack for {_DEMO_COMPANY} ({partner_name})"
        description = f"{base_desc}\n{note}" if note else base_desc
        props = {
            "dealname": dealname[:200],
            "description": description[:1000],
        }
        amount = payload.get("amount")
        if amount not in (None, ""):
            props["amount"] = str(amount)
        stage = str(payload.get("deal_stage") or "").strip()
        if stage:
            props["dealstage"] = stage

        tenant = getattr(request, "tenant", None)
        try:
            api = HubspotApiService.for_tenant(tenant)
            created = api.create_deal(props)
        except HubspotNotConnected as exc:
            result = service_result(
                "HubSpotCreateDeal",
                status="error",
                error="not_connected",
                detail=str(exc),
            )
            maybe_save_callback(
                request,
                instruction_row,
                result,
                description="HubSpotCreateDeal not connected",
            )
            return result
        except HubspotApiError as exc:
            logger.error("[HubSpotCreateDeal] %s", exc)
            result = service_result(
                "HubSpotCreateDeal",
                status="error",
                error="api_error",
                detail=str(exc),
            )
            maybe_save_callback(
                request,
                instruction_row,
                result,
                description="HubSpotCreateDeal API error",
            )
            return result
        except Exception as exc:
            logger.error("[HubSpotCreateDeal] unexpected: %s", exc)
            result = service_result(
                "HubSpotCreateDeal",
                status="error",
                error="error",
                detail=str(exc),
            )
            maybe_save_callback(
                request,
                instruction_row,
                result,
                description="HubSpotCreateDeal error",
            )
            return result

        deal_id = created.get("id")
        result = service_result(
            "HubSpotCreateDeal",
            status="success",
            deal_id=deal_id,
            dealname=dealname,
            partner_name=partner_name,
            reference=reference,
            created=True,
        )
        maybe_save_callback(
            request,
            instruction_row,
            result,
            description=f"HubSpot deal created: {dealname}",
        )
        return result


def _extract_sale_payload(request) -> dict:
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
