"""
SlackCaptureContacts — paginated users.list into Captured Topics.

Endpoint bookmark: Capture contacts (direct_event slack.capture_contacts).

Requires a Slack bot token with ``users:read`` (and usually ``users:read.email``)
on TenantApp.extra_config — keys tried: bot_token, slack_bot_token, slack_token,
access_token — or settings SLACK_BOT_TOKEN.
"""
from __future__ import annotations

import logging
import os

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

SLACK_API = "https://slack.com/api"


class SlackCaptureContacts(AtomicServiceBase):
    atomic_apps = ("slack",)
    atomic_category = "read"

    @staticmethod
    def get_parameters(parameters, key="SlackCaptureContacts"):
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
                "SlackCaptureContacts",
                status="error",
                error="no_tenant",
                detail="No tenant on request",
            )

        creds = _resolve_slack_token(tenant)
        if not creds.get("ok"):
            return service_result(
                "SlackCaptureContacts",
                status="error",
                error=creds.get("error") or "no_token",
                detail=creds.get("detail")
                or "Set TenantApp.extra_config.bot_token (xoxb-…) with users:read",
                slack={},
            )

        token = creds["token"]
        max_rows = PAGE_SIZE * MAX_CONTACT_PAGES
        try:
            mq = getattr(request, "mq_message_data", None) if request is not None else None
            if isinstance(mq, dict) and mq.get("limit") not in (None, ""):
                max_rows = max(1, min(int(mq.get("limit")), PAGE_SIZE * MAX_CONTACT_PAGES))
        except (TypeError, ValueError):
            pass

        try:
            raw_users = _list_all_users(token, max_rows=max_rows)
        except Exception as exc:
            logger.error("[SlackCaptureContacts] %s", exc)
            return service_result(
                "SlackCaptureContacts",
                status="error",
                error="error",
                detail=str(exc),
                slack={},
            )

        if isinstance(raw_users, dict) and raw_users.get("error"):
            return service_result(
                "SlackCaptureContacts",
                status="error",
                error=raw_users.get("error") or "slack_api",
                detail=raw_users.get("detail") or "",
                slack={},
            )

        contacts = []
        for u in raw_users:
            if not isinstance(u, dict):
                continue
            if u.get("is_bot") or u.get("id") == "USLACKBOT":
                continue
            profile = u.get("profile") if isinstance(u.get("profile"), dict) else {}
            name = (
                profile.get("real_name")
                or u.get("real_name")
                or u.get("name")
                or ""
            )
            contacts.append(
                normalize_contact(
                    source_app="slack",
                    external_id=u.get("id"),
                    name=name,
                    email=profile.get("email") or "",
                    phone=profile.get("phone") or "",
                    company="",
                    username=u.get("name") or "",
                    active=not bool(u.get("deleted")),
                    raw_record=u,
                )
            )

        actor = "system"
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "username", None):
            actor = str(user.username)

        enroll = enroll_contact_capture(
            tenant=tenant,
            source_app="slack",
            records=contacts,
            actor=actor,
            action_path="slack/contacts",
            event_key="slack.capture_contacts",
            method="GET",
        )

        result = service_result(
            "SlackCaptureContacts",
            status="success" if enroll.get("success") else "error",
            count=len(contacts),
            contacts=contacts,
            slack={"team_id": creds.get("team_id") or ""},
            mailbox=enroll,
            topic=enroll.get("topic"),
            mailbox_id=enroll.get("mailbox_id"),
        )
        if not enroll.get("success"):
            result["error"] = enroll.get("error") or "mailbox_enroll_failed"
            result["detail"] = result["error"]
        return result


def _resolve_slack_token(tenant) -> dict:
    from django.conf import settings

    from dose.tenant_app_lookup import get_tenant_app_in_schema

    ta = get_tenant_app_in_schema(tenant, "slack")
    team_id = ""
    token = ""
    if ta is not None:
        extra = ta.extra_config if isinstance(ta.extra_config, dict) else {}
        team_id = str(extra.get("slack_team_id") or "")
        for key in (
            "bot_token",
            "slack_bot_token",
            "slack_token",
            "access_token",
            "xoxb_token",
        ):
            val = (extra.get(key) or "").strip()
            if val:
                token = val
                break

    if not token:
        token = (
            str(getattr(settings, "SLACK_BOT_TOKEN", "") or "").strip()
            or os.environ.get("SLACK_BOT_TOKEN", "").strip()
        )

    if not token:
        return {
            "ok": False,
            "error": "no_slack_token",
            "detail": (
                "Missing Slack bot token. Set TenantApp.extra_config.bot_token "
                "(xoxb-…) with users:read (+ users:read.email for emails)."
            ),
        }
    return {"ok": True, "token": token, "team_id": team_id}


def _list_all_users(token: str, *, max_rows: int) -> list | dict:
    headers = {"Authorization": f"Bearer {token}"}
    out: list = []
    cursor = None
    while len(out) < max_rows:
        params = {"limit": min(200, max_rows - len(out))}
        if cursor:
            params["cursor"] = cursor
        resp = http_requests.get(
            f"{SLACK_API}/users.list",
            headers=headers,
            params=params,
            timeout=30,
        )
        if resp.status_code >= 400:
            return {
                "error": f"http_{resp.status_code}",
                "detail": (resp.text or "")[:500],
            }
        data = resp.json() if resp.content else {}
        if not data.get("ok"):
            return {
                "error": data.get("error") or "slack_not_ok",
                "detail": str(data)[:500],
            }
        members = data.get("members") or []
        if not isinstance(members, list) or not members:
            break
        out.extend(members)
        cursor = (data.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            break
    return out
