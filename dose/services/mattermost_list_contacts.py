"""
MattermostListContacts — paginated GET /api/v4/users into Captured Topics.

Endpoint bookmark: Capture contacts (direct_event mattermost.capture_contacts).
"""
from __future__ import annotations

import logging

import requests as http_requests

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_service_utils import service_result
from dose.services.atomic_services_registry import filter_parameters_for_service
from dose.services.contact_capture import (
    MAX_CONTACT_PAGES,
    PAGE_SIZE,
    enroll_contact_capture,
    normalize_contact,
)

logger = logging.getLogger(__name__)


class MattermostListContacts(AtomicServiceBase):
    atomic_apps = ("mattermost",)
    atomic_category = "read"

    @staticmethod
    def get_parameters(parameters, key="MattermostListContacts"):
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
        if tenant is None or not getattr(tenant, "schema_name", None):
            return service_result(
                "MattermostListContacts",
                status="error",
                error="no_tenant",
                detail="No tenant on request",
            )

        creds = _resolve_mm_creds(tenant)
        if not creds.get("ok"):
            return service_result(
                "MattermostListContacts",
                status="error",
                error=creds.get("error") or "mm_creds",
                detail=creds.get("detail") or "Missing Mattermost URL or token",
                mattermost={"url": creds.get("url") or ""},
            )

        mm_url = creds["url"]
        token = creds["token"]
        headers = {"Authorization": f"Bearer {token}"}

        max_rows = PAGE_SIZE * MAX_CONTACT_PAGES
        try:
            mq = getattr(request, "mq_message_data", None) if request is not None else None
            if isinstance(mq, dict) and mq.get("limit") not in (None, ""):
                max_rows = max(1, min(int(mq.get("limit")), PAGE_SIZE * MAX_CONTACT_PAGES))
        except (TypeError, ValueError):
            pass

        raw_users = []
        try:
            page = 0
            while len(raw_users) < max_rows:
                per_page = min(PAGE_SIZE, max_rows - len(raw_users))
                resp = http_requests.get(
                    f"{mm_url}/api/v4/users",
                    headers=headers,
                    params={"page": page, "per_page": per_page},
                    timeout=30,
                )
                if resp.status_code >= 400:
                    return service_result(
                        "MattermostListContacts",
                        status="error",
                        error=f"http_{resp.status_code}",
                        detail=(resp.text or "")[:500],
                        mattermost={"url": mm_url},
                    )
                batch = resp.json()
                if not isinstance(batch, list) or not batch:
                    break
                raw_users.extend(batch)
                if len(batch) < per_page:
                    break
                page += 1
        except Exception as exc:
            logger.error("[MattermostListContacts] %s", exc)
            return service_result(
                "MattermostListContacts",
                status="error",
                error="error",
                detail=str(exc),
                mattermost={"url": mm_url},
            )

        contacts = []
        for u in raw_users:
            if not isinstance(u, dict):
                continue
            first = (u.get("first_name") or "").strip()
            last = (u.get("last_name") or "").strip()
            display = f"{first} {last}".strip() or (u.get("username") or "")
            contacts.append(
                normalize_contact(
                    source_app="mattermost",
                    external_id=u.get("id"),
                    name=display,
                    email=u.get("email") or "",
                    phone="",
                    company="",
                    username=u.get("username") or "",
                    active=not bool(u.get("delete_at")),
                    raw_record=u,
                )
            )

        actor = "system"
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "username", None):
            actor = str(user.username)

        enroll = enroll_contact_capture(
            tenant=tenant,
            source_app="mattermost",
            records=contacts,
            actor=actor,
            action_path="mattermost/contacts",
            event_key="mattermost.capture_contacts",
            method="GET",
        )

        result = service_result(
            "MattermostListContacts",
            status="success" if enroll.get("success") else "error",
            count=len(contacts),
            contacts=contacts,
            mattermost={"url": mm_url},
            mailbox=enroll,
            topic=enroll.get("topic"),
            mailbox_id=enroll.get("mailbox_id"),
        )
        if not enroll.get("success"):
            result["error"] = enroll.get("error") or "mailbox_enroll_failed"
            result["detail"] = result["error"]
        return result


def _resolve_mm_creds(tenant) -> dict:
    """URL + token from TenantApp.extra_config / PassThroughEndpoint / settings."""
    from dose.tenant_app_lookup import get_tenant_app_in_schema, tenant_schema_search_path

    url = ""
    token = ""
    ta = get_tenant_app_in_schema(tenant, "mattermost")
    if ta is None:
        # fuzzy match
        from dose.models import TenantApp

        with tenant_schema_search_path(tenant) as ok:
            if ok:
                ta = (
                    TenantApp.objects.filter(app_name__icontains="mattermost")
                    .order_by("-id")
                    .first()
                )
    if ta is not None:
        extra = ta.extra_config if isinstance(ta.extra_config, dict) else {}
        url = (extra.get("mm_url") or extra.get("url") or "").strip().rstrip("/")
        token = (
            extra.get("mm_token")
            or extra.get("mmauthtoken")
            or extra.get("admin_token")
            or ""
        ).strip()

    if not url:
        from dose.models import PassThroughEndpoint

        with tenant_schema_search_path(tenant) as ok:
            if ok:
                for ep in PassThroughEndpoint.objects.all():
                    eu = (getattr(ep, "endpoint_url", "") or "").lower()
                    slug = (getattr(ep, "slug", "") or "").lower()
                    if "mattermost" in eu or "mattermost" in slug or ":8065" in eu:
                        url = (ep.endpoint_url or "").rstrip("/")
                        break

    if not url:
        try:
            from dose.services.mattermost_tenant_provisioner import _get_mattermost_base_url

            url = _get_mattermost_base_url()
        except Exception:
            url = ""

    if not url:
        return {"ok": False, "error": "no_mm_url", "detail": "Mattermost URL not configured"}
    if not token:
        return {
            "ok": False,
            "error": "no_mm_token",
            "detail": "Mattermost token missing on TenantApp.extra_config",
            "url": url,
        }
    return {"ok": True, "url": url, "token": token}
