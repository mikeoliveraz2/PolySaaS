"""
HubSpotCaptureContacts — paginated HubSpot CRM contacts into Captured Topics.

Endpoint bookmark: Capture contacts (direct_event hubspot.capture_contacts).
"""
from __future__ import annotations

import logging

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import service_result
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.contact_capture import (
    MAX_CONTACT_PAGES,
    PAGE_SIZE,
    enroll_contact_capture,
    normalize_contact,
)
from dose.services.hubspot_api import HubspotApiError, HubspotApiService, HubspotNotConnected

logger = logging.getLogger(__name__)

_PROPS = ("firstname", "lastname", "email", "phone", "company")


class HubSpotCaptureContacts(AtomicServiceBase):
    atomic_apps = ("hubspot",)
    atomic_category = "read"

    @staticmethod
    def get_parameters(parameters, key="HubSpotCaptureContacts"):
        return filter_parameters_for_service(parameters, key)

    @staticmethod
    def execute_and_save(request, instruction_row=None):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            try:
                from dose.utils import get_current_tenant

                tenant = get_current_tenant(request)
            except Exception:
                tenant = None

        max_rows = PAGE_SIZE * MAX_CONTACT_PAGES
        try:
            mq = getattr(request, "mq_message_data", None) if request is not None else None
            if isinstance(mq, dict) and mq.get("limit") not in (None, ""):
                max_rows = max(1, min(int(mq.get("limit")), PAGE_SIZE * MAX_CONTACT_PAGES))
        except (TypeError, ValueError):
            pass

        hubspot_meta = {}
        try:
            api = HubspotApiService.for_tenant(tenant)
            hubspot_meta = {
                "portal_id": (api._extra().get("hs_portal_id") or ""),
                "token_type": (api._extra().get("hs_token_type") or ""),
            }
            raw = _list_all_contacts(api, max_rows=max_rows)
        except HubspotNotConnected as exc:
            return service_result(
                "HubSpotCaptureContacts",
                status="error",
                error="not_connected",
                detail=str(exc),
                hubspot=hubspot_meta,
            )
        except HubspotApiError as exc:
            logger.error("[HubSpotCaptureContacts] %s", exc)
            return service_result(
                "HubSpotCaptureContacts",
                status="error",
                error="api_error",
                detail=str(exc),
                hubspot=hubspot_meta,
            )
        except Exception as exc:
            logger.error("[HubSpotCaptureContacts] unexpected: %s", exc)
            return service_result(
                "HubSpotCaptureContacts",
                status="error",
                error="error",
                detail=str(exc),
                hubspot=hubspot_meta,
            )

        contacts = []
        for row in raw:
            first = row.get("firstname") or ""
            last = row.get("lastname") or ""
            name = f"{first} {last}".strip() or (row.get("email") or f"#{row.get('id')}")
            contacts.append(
                normalize_contact(
                    source_app="hubspot",
                    external_id=row.get("id"),
                    name=name,
                    email=row.get("email") or "",
                    phone=row.get("phone") or "",
                    company=row.get("company") or "",
                    username="",
                    active=True,
                    raw_record=row,
                )
            )

        actor = "system"
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "username", None):
            actor = str(user.username)

        enroll = enroll_contact_capture(
            tenant=tenant,
            source_app="hubspot",
            records=contacts,
            actor=actor,
            action_path="hubspot/contacts",
            event_key="hubspot.capture_contacts",
            method="GET",
        )

        result = service_result(
            "HubSpotCaptureContacts",
            status="success" if enroll.get("success") else "error",
            count=len(contacts),
            contacts=contacts,
            hubspot=hubspot_meta,
            mailbox=enroll,
            topic=enroll.get("topic"),
            mailbox_id=enroll.get("mailbox_id"),
        )
        if not enroll.get("success"):
            result["error"] = enroll.get("error") or "mailbox_enroll_failed"
            result["detail"] = result["error"]
        return result


def _list_all_contacts(api: HubspotApiService, *, max_rows: int) -> list[dict]:
    """Paginate HubSpot contacts.basic_api.get_page (does not edit hubspot_api.py)."""
    client = api.client()
    basic = client.crm.contacts.basic_api
    out: list[dict] = []
    after = None
    while len(out) < max_rows:
        limit = min(100, max_rows - len(out))  # HubSpot page max is 100
        kwargs = {"limit": limit, "properties": list(_PROPS)}
        if after:
            kwargs["after"] = after
        page = basic.get_page(**kwargs)
        batch = api._props_list(getattr(page, "results", None), list(_PROPS))
        if not batch:
            break
        out.extend(batch)
        paging = getattr(page, "paging", None)
        next_page = getattr(paging, "next", None) if paging else None
        after = getattr(next_page, "after", None) if next_page else None
        if not after:
            break
    return out
