"""Authenticated demo webhooks used by the three Slack wireframe surfaces."""
from __future__ import annotations

import json
import uuid

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from dose.polysniffer.sniff_tenant import bind_request_tenant
from dose.tenant_app_lookup import tenant_schema_search_path
from dose.webhook_events import publish_slack_wireframe_event


@staff_member_required
@require_POST
def slack_wireframe_trigger(request, kind: str):
    if kind not in ("contact", "sale"):
        return JsonResponse(
            {"success": False, "error": "unsupported event"},
            status=404,
        )
    tenant = bind_request_tenant(request)
    if not tenant:
        return JsonResponse(
            {"success": False, "error": "no tenant context"},
            status=400,
        )
    try:
        supplied = json.loads(request.body or b"{}")
    except (TypeError, ValueError):
        supplied = {}
    supplied = supplied if isinstance(supplied, dict) else {}
    payload = _demo_payload(kind, supplied)
    result = publish_slack_wireframe_event(tenant, kind, payload)
    return JsonResponse(result, status=202 if result.get("success") else 503)


@staff_member_required
@require_GET
def slack_wireframe_status(request, mailbox_id: int):
    tenant = bind_request_tenant(request)
    if not tenant:
        return JsonResponse(
            {"success": False, "error": "no tenant context"},
            status=400,
        )
    from dose.models import WebhookMailbox

    with tenant_schema_search_path(tenant) as ok:
        if not ok:
            return JsonResponse(
                {"success": False, "error": "invalid tenant schema"},
                status=400,
            )
        mailbox = WebhookMailbox.objects.filter(pk=mailbox_id).first()
        if not mailbox:
            return JsonResponse(
                {"success": False, "error": "mailbox event not found"},
                status=404,
            )
        return JsonResponse(
            {
                "success": True,
                "status": mailbox.status,
                "result": mailbox.result,
                "error": mailbox.error,
            }
        )


@staff_member_required
@require_GET
def slack_wireframe_messages(request):
    tenant = bind_request_tenant(request)
    if not tenant:
        return JsonResponse(
            {"success": False, "error": "no tenant context"},
            status=400,
        )
    from dose.messaging import list_recent_messages

    return JsonResponse(
        {
            "success": True,
            "messages": list_recent_messages(
                tenant=tenant,
                user=request.user if request.user.is_authenticated else None,
            ),
        }
    )


@staff_member_required
@require_POST
def slack_wireframe_post_message(request):
    tenant = bind_request_tenant(request)
    if not tenant:
        return JsonResponse(
            {"success": False, "error": "no tenant context"},
            status=400,
        )
    try:
        body = json.loads(request.body or b"{}")
    except (TypeError, ValueError):
        body = {}
    text = (body.get("message") or "").strip() if isinstance(body, dict) else ""
    if not text:
        return JsonResponse(
            {"success": False, "error": "message required"},
            status=400,
        )
    from dose.messaging import create_dose_message, list_recent_messages

    row = create_dose_message(
        tenant=tenant,
        user=request.user if request.user.is_authenticated else None,
        message=text,
        level="info",
    )
    if row is None:
        return JsonResponse(
            {"success": False, "error": "could not save message"},
            status=500,
        )
    return JsonResponse(
        {
            "success": True,
            "message": {
                "id": row.id,
                "message": row.message,
                "level": row.level,
                "author": getattr(request.user, "username", None) or "you",
                "created_at": row.created_at.isoformat() if row.created_at else "",
            },
            "messages": list_recent_messages(
                tenant=tenant,
                user=request.user if request.user.is_authenticated else None,
            ),
        }
    )


def _demo_payload(kind: str, supplied: dict) -> dict:
    token = uuid.uuid4().hex[:10]
    stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    if kind == "contact":
        payload = {
            "demo_id": token,
            "name": supplied.get("name") or f"Slack Contact {stamp}",
            "email": supplied.get("email") or f"slack.contact.{token}@example.com",
            "phone": supplied.get("phone") or "+1 555 0100",
            "is_company": str(supplied.get("is_company") or "").lower()
            in ("1", "true", "yes", "company"),
        }
        for field in ("street", "city", "zip"):
            value = (supplied.get(field) or "").strip()
            if value:
                payload[field] = value[:120]
        return payload
    return {
        "demo_id": token,
        "partner_name": supplied.get("partner_name") or f"Slack Buyer {stamp}",
        "partner_email": supplied.get("partner_email") or f"slack.buyer.{token}@example.com",
        "order_reference": supplied.get("order_reference") or f"SLACK-{stamp}-{token[:4]}",
        "note": supplied.get("note") or "Draft quotation created from the PolySaaS Slack wireframe.",
    }
