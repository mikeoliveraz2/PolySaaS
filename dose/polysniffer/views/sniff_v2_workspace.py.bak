"""Admin-only PolySniffer control screen with top-level browser launches."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24
#
# FIX 2026-08-20 (owner-approved, frozen-file exception): sniff_shell() resolved
# the endpoint correctly (via ?schema= or session), but the browser-launch URLs
# it handed to the client (/pt/polysniff/<id>/...) carried no schema hint at
# all. AdminTenantSessionMiddleware resets request.session['tenant_slug'] back
# to the logged-in staff user's own home tenant on every response, so by the
# time the client's <object data="..."> fetched that URL, session-based
# resolution in get_endpoint_any_schema() pointed at the wrong tenant and
# 404'd -- rendering as a blank pane (confirmed via direct repro: same
# endpoint_id resolves 200 under the correct tenant, 404 under the reset one).
# This only showed up for endpoints owned by a tenant other than the staff
# user's own (e.g. Slack under 'olient' while admin's home tenant is
# 'polysaas'); Odoo/Mattermost never exposed it because they happened to match.
# Now the endpoint's authoritative schema (already resolved once via
# get_endpoint_by_host) is threaded through to the client as an explicit
# ?schema= query param on the native/passthrough launch URLs, so resolution
# never depends on session state that this same request cycle is about to
# overwrite.
# BINGO: PolySniffer Cross-Tenant Launch URL Schema Fix — 2026-08-20
#
# FIX 2026-08-21 SUPERSEDED by POLYSNIFFER_NATIVE_FORWARDER north star:
# Native = /admin/polysniffer/sniff/<host>/native/ (no green bar).
# Passthrough = workspace/passthrough with orchestration bar + consumer bind.
# Do not launch Native via /pt/polysniff/ (that path is passthrough-mode).
# Owner-approved 2026-08-23: Slack wireframe Live events pane — mailbox +
# DoseMessage in workspace poll; suppress HAR noise while wireframe is on.
from __future__ import annotations

import json
import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from dose.polysniffer.har_capture import _ensure_tenant_schema
from dose.polysniffer.sniff_tenant import bind_request_tenant, get_sniff_capture_session
from dose.polysniffer.models import TrafficLog
from dose.polysniffer.schema_patch import ensure_trafficlog_capture_columns
from dose.models import TenantApp
from dose.polysniffer.views.core import get_endpoint_by_host
from dose.passthrough.registry import resolve_handler_for_endpoint

logger = logging.getLogger(__name__)


def _endpoint_label(endpoint) -> str:
    return endpoint.menu_title or endpoint.endpoint_url or f"Endpoint {endpoint.pk}"


def _session_mode(request, endpoint_host: str) -> str:
    mode = (request.session.get(f"polysniffer_{endpoint_host}_mode") or "").strip().lower()
    return mode if mode in ("native", "passthrough") else ""


def _native_browse_subpath(endpoint) -> str:
    """Return only the endpoint's configured starting path for raw Native mode."""
    path = (getattr(endpoint, "starting_uri", None) or "/").strip()
    if not path.startswith("/"):
        path = f"/{path}"
    return path


def _mailbox_context(endpoint) -> dict:
    """Return handler-declared webhook/mailbox plumbing, if any."""
    handler = resolve_handler_for_endpoint(endpoint)
    hook = getattr(handler, "polysniffer_mailbox_context", None)
    if not callable(hook):
        return {}
    return hook(endpoint) or {}


def _wireframe_context(endpoint) -> dict:
    """Return handler-owned demo surface configuration, if declared."""
    handler = resolve_handler_for_endpoint(endpoint)
    hook = getattr(handler, "polysniffer_wireframe_context", None)
    if not callable(hook):
        return {}
    context = hook(endpoint) or {}
    return context if context.get("enabled") else {}


def _include_mailbox_in_poll(*, mode: str, wireframe: bool, source: str) -> bool:
    """Passthrough always; Native only when the Slack wireframe event pane is on."""
    if not source:
        return False
    return mode == "passthrough" or bool(wireframe)


def _mailbox_outcome(result) -> str:
    if not isinstance(result, dict):
        return ""
    for atomic in result.get("results") or []:
        if not isinstance(atomic, dict):
            continue
        if atomic.get("partner_id"):
            return f"partner #{atomic['partner_id']}"
        if atomic.get("order_name") or atomic.get("order_id"):
            return str(atomic.get("order_name") or f"order #{atomic.get('order_id')}")
        if atomic.get("status") in ("error", "failed"):
            return str(atomic.get("detail") or atomic.get("error") or "error")
    return str(result.get("status") or "")


def _mailbox_transaction_state(row_status: str, result) -> str:
    """Normalize mailbox + atomic results for both orchestration bars."""
    if row_status in ("pending", "claimed", "failed", "expired"):
        return row_status
    if row_status != "processed" or not isinstance(result, dict):
        return row_status or "unknown"
    if result.get("status") == "no_instruction" or result.get("matched", 0) == 0:
        return "no_consumer"
    atomic_results = [
        item for item in (result.get("results") or []) if isinstance(item, dict)
    ]
    if any(item.get("status") in ("error", "failed") for item in atomic_results):
        return "failed"
    if any(item.get("status") == "success" for item in atomic_results):
        return "success"
    return "processed"


def _serialize_mailbox_event(row) -> dict:
    """Expose action evidence without leaking Slack tokens/response URLs."""
    envelope = row.envelope or {}
    raw_payload = envelope.get("payload") or {}
    allowed_payload = {
        "command",
        "text",
        "user_id",
        "user_name",
        "channel_id",
        "channel_name",
        "team_id",
        # Slack wireframe demo fields
        "demo_id",
        "name",
        "email",
        "phone",
        "partner_name",
        "partner_email",
        "order_reference",
        "note",
    }
    payload = {
        key: raw_payload.get(key)
        for key in allowed_payload
        if raw_payload.get(key) not in (None, "")
    }
    result = row.result if isinstance(row.result, dict) else {}
    return {
        "id": row.id,
        "source": row.source,
        "event_key": envelope.get("event_key", ""),
        "action_path": row.action_path,
        "method": envelope.get("method", "POST"),
        "direction": envelope.get("direction", "REQ"),
        "status": row.status,
        "transaction_state": _mailbox_transaction_state(row.status, result),
        "result_status": result.get("status", ""),
        "matched": result.get("matched", 0),
        "executed": result.get("executed", len(result.get("results") or [])),
        "outcome": _mailbox_outcome(result),
        "error": (row.error or "")[:500],
        "payload": payload,
        "created_at": row.created_at.strftime("%H:%M:%S") if row.created_at else "",
        "processed_at": row.processed_at.strftime("%H:%M:%S") if row.processed_at else "",
    }


def _serialize_dose_message(row) -> dict:
    return {
        "id": row.id,
        "message": row.message,
        "level": row.level,
        "author": "PolySaaS" if row.user_id is None else "you",
        "created_at": row.created_at.strftime("%H:%M:%S") if row.created_at else "",
    }


@staff_member_required
def sniff_shell(request, endpoint_host: str, mode: str | None = None, browse_path: str = ""):
    """PolySniffer workspace — native capture (no orch bar) or passthrough + green bar."""
    try:
        endpoint = get_endpoint_by_host(endpoint_host, request)
    except Exception as exc:
        return render(
            request,
            "polysniffer/sniff_workspace.html",
            {"error": str(exc), "endpoint_host": endpoint_host},
            status=404,
        )
    active_mode = (mode or "").strip().lower()
    if active_mode in ("native", "passthrough"):
        from dose.polysniffer.sniff_session_utils import ensure_capture_session

        ensure_capture_session(request, endpoint_host, active_mode)
    else:
        request.session.pop(f"polysniffer_{endpoint_host}_capture", None)
        request.session.pop(f"polysniffer_{endpoint_host}_mode", None)
        active_mode = ""
    request.session.modified = True

    upstream_url = (getattr(endpoint, "endpoint_url", None) or "").strip().rstrip("/")
    browse_subpath = _native_browse_subpath(endpoint)
    upstream_browse_url = f"{upstream_url}{browse_subpath}" if upstream_url else ""
    active_session = get_sniff_capture_session(request, endpoint_host) if active_mode else None
    wireframe = _wireframe_context(endpoint)

    app_launch_url = ""
    pt_embed_ctx = None
    native_embed_ctx = None
    if active_session and wireframe:
        wireframe_body = render_to_string(
            "polysniffer/slack_wireframe.html",
            {"slack_wireframe_mode": active_mode},
            request=request,
        )
        if active_mode == "native":
            native_embed_ctx = {"native_embed_body": mark_safe(wireframe_body)}
        elif active_mode == "passthrough":
            orch_bar = render_to_string(
                "polysniffer/sniff_pt_orchestration_bar.html",
                request=request,
            )
            pt_embed_ctx = {
                "passthrough_embed_body": mark_safe(orch_bar + wireframe_body)
            }
    elif active_session and active_mode == "native":
        # FIX 2026-08-21 (owner-approved): Inline Native — embed forwarder HTML in
        # the workspace left pane (no <object>, no iframe). Same pattern as
        # Passthrough inline, without the green orchestration bar.
        native_subpath = (browse_path or browse_subpath or "/").strip()
        if not native_subpath.startswith("/"):
            native_subpath = f"/{native_subpath}"
        schema = getattr(request, "schema_name", "") or ""
        q = f"?_ps_tenant={schema}" if schema else ""
        app_launch_url = (
            f"/admin/polysniffer/sniff/{endpoint_host}/workspace/native"
            f"{native_subpath}{q}"
        )
        try:
            from dose.polysniffer.sniff_native_embed import build_inline_native_embed_context

            native_embed_ctx = build_inline_native_embed_context(
                request,
                endpoint.pk,
                endpoint,
                native_subpath,
                endpoint_label=_endpoint_label(endpoint),
                endpoint_host=endpoint_host,
            )
            if native_embed_ctx and native_embed_ctx.get("redirect"):
                from django.shortcuts import redirect

                return redirect(native_embed_ctx["redirect"])
        except Exception:
            logger.exception("native inline embed build failed")
    elif active_session and active_mode == "passthrough":
        frame_subpath = (browse_path or browse_subpath or "/").strip()
        if not frame_subpath.startswith("/"):
            frame_subpath = f"/{frame_subpath}"
        app_launch_url = (
            f"{endpoint.get_proxy_prefix().rstrip('/')}"
            f"{frame_subpath}"
        )
        try:
            from dose.polysniffer.sniff_pt_embed import build_inline_passthrough_embed_context

            pt_embed_ctx = build_inline_passthrough_embed_context(
                request,
                endpoint.pk,
                endpoint,
                frame_subpath,
                endpoint_label=_endpoint_label(endpoint),
            )
        except Exception:
            logger.exception("passthrough inline embed build failed")

    workspace_prefix = f"/admin/polysniffer/sniff/{endpoint_host}"
    poll_url = f"{workspace_prefix}/workspace/poll/"
    schema = getattr(request, "schema_name", "") or ""

    context = {
        "endpoint": endpoint,
        "endpoint_host": endpoint_host,
        "endpoint_label": _endpoint_label(endpoint),
        "mode": active_mode,
        "app_launch_url": app_launch_url,
        "browse_subpath": browse_subpath,
        "upstream_browse_url": upstream_browse_url,
        "active_session": active_session,
        "diff_url": f"{workspace_prefix}/diff/",
        "export_url": f"{workspace_prefix}/export-har/",
        "poll_url": poll_url,
        "schema": schema,
        "native_top_level": False,
        "wireframe_enabled": bool(wireframe),
    }
    if native_embed_ctx:
        context.update(native_embed_ctx)
    if pt_embed_ctx:
        context.update(pt_embed_ctx)

    return render(
        request,
        "polysniffer/sniff_workspace.html",
        context,
    )


# Alias retained for Python callers; it resolves to the same canonical screen.
sniff_workspace = sniff_shell


@staff_member_required
@require_GET
def workspace_poll(request, endpoint_host: str):
    try:
        tenant = bind_request_tenant(request)
        if not tenant:
            return JsonResponse({"success": False, "error": "no tenant context"}, status=400)

        endpoint = get_endpoint_by_host(endpoint_host, request)
        mailbox_context = _mailbox_context(endpoint)
        wireframe_context = _wireframe_context(endpoint)

        ensure_trafficlog_capture_columns(request)
        _ensure_tenant_schema(tenant)

        mode = (request.GET.get("mode") or _session_mode(request, endpoint_host) or "native").strip().lower()
        if mode not in ("native", "passthrough"):
            mode = "native"

        try:
            since_id = int(request.GET.get("since_id", 0))
        except (TypeError, ValueError):
            since_id = 0
        try:
            mailbox_since_id = int(request.GET.get("mailbox_since_id", 0))
        except (TypeError, ValueError):
            mailbox_since_id = 0
        try:
            messages_since_id = int(request.GET.get("messages_since_id", 0))
        except (TypeError, ValueError):
            messages_since_id = 0

        session = get_sniff_capture_session(request, endpoint_host)
        wireframe_mode = bool(wireframe_context)

        try:
            def _preview(text):
                return (text or "")[:500]

            def _more(text):
                return len(text or "") > 500

            captures = []
            if not wireframe_mode:
                qs = TrafficLog.objects.all()
                if session:
                    qs = qs.filter(capture_session=session)
                else:
                    if mode == "passthrough":
                        qs = qs.filter(client_path__contains=f"/pt/admin/{endpoint_host}")
                    else:
                        qs = qs.filter(client_path__contains=f"/sniff/{endpoint_host}/")

                if not session:
                    qs = qs.filter(capture_source=mode)
                if since_id:
                    qs = qs.filter(id__gt=since_id)
                    logs = list(qs.order_by("id")[:100])
                else:
                    # Initial backfill: newest rows first in UI (client prepends in id order).
                    logs = list(qs.order_by("-id")[:100])
                    logs.reverse()

                captures = [
                    {
                        "id": log.id,
                        "method": log.method,
                        "url": log.url,
                        "path": log.path,
                        "client_path": log.client_path,
                        "status_code": log.status_code,
                        "capture_source": log.capture_source,
                        "captured_at": log.captured_at.strftime("%H:%M:%S") if log.captured_at else "",
                        "duration_ms": log.duration_ms,
                        "headers": log.headers or {},
                        "cookies": getattr(log, "cookies", None) or {},
                        "query_params": log.query_params or {},
                        "body_preview": _preview(log.body or ""),
                        "body_more": _more(log.body or ""),
                        "response_headers": log.response_headers or {},
                        "response_body_preview": _preview(log.response_body or ""),
                        "response_body_more": _more(log.response_body or ""),
                    }
                    for log in logs
                ]

            mailbox_events = []
            if _include_mailbox_in_poll(
                mode=mode,
                wireframe=wireframe_mode,
                source=mailbox_context.get("source") or "",
            ):
                from dose.models import WebhookMailbox

                mailbox_qs = WebhookMailbox.objects.filter(
                    source=mailbox_context["source"]
                )
                if mailbox_since_id:
                    mailbox_qs = mailbox_qs.filter(id__gt=mailbox_since_id)
                else:
                    mailbox_qs = mailbox_qs.order_by("-id")[:100]
                mailbox_rows = list(mailbox_qs.order_by("id")[:100]) if mailbox_since_id else list(mailbox_qs)
                mailbox_rows.sort(key=lambda row: row.id)

                for row in mailbox_rows:
                    mailbox_events.append(_serialize_mailbox_event(row))

            messages = []
            if wireframe_mode:
                from django.db.models import Q

                from dose.models import DoseMessage

                msg_qs = DoseMessage.objects.all()
                user = getattr(request, "user", None)
                if user is not None and getattr(user, "is_authenticated", False):
                    msg_qs = msg_qs.filter(Q(user_id=user.pk) | Q(user_id__isnull=True))
                if messages_since_id:
                    msg_qs = msg_qs.filter(id__gt=messages_since_id)
                    msg_rows = list(msg_qs.order_by("id")[:100])
                else:
                    msg_rows = list(msg_qs.order_by("-id")[:50])
                    msg_rows.reverse()
                messages = [_serialize_dose_message(row) for row in msg_rows]
        except Exception as exc:
            return JsonResponse(
                {
                    "success": True,
                    "captures": [],
                    "mailbox_events": [],
                    "messages": [],
                    "wireframe_enabled": wireframe_mode,
                    "session_active": bool(session),
                    "session_name": session.capture_name if session else "",
                    "mode": mode,
                    "warning": str(exc),
                }
            )

        return JsonResponse(
            {
                "success": True,
                "captures": captures,
                "mailbox_events": mailbox_events,
                "messages": messages,
                "wireframe_enabled": wireframe_mode,
                "session_active": bool(session),
                "session_name": session.capture_name if session else "",
                "mode": mode,
            }
        )
    except Exception as exc:
        logger.exception("workspace_poll failed")
        return JsonResponse(
            {
                "success": True,
                "captures": [],
                "mailbox_events": [],
                "messages": [],
                "wireframe_enabled": False,
                "session_active": False,
                "session_name": "",
                "mode": "native",
                "warning": str(exc),
            },
            status=200,
        )


@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def store_mm_token(request, endpoint_host: str):
    """Store browser MMAUTHTOKEN in TenantApp so passthrough can use it server-side."""
    try:
        get_endpoint_by_host(endpoint_host, request)
    except Exception as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    token = (
        request.POST.get("token") or
        request.COOKIES.get("MMAUTHTOKEN") or
        request.COOKIES.get("mmauthtoken") or
        ""
    ).strip()
    if not token:
        return JsonResponse({"ok": False, "error": "no MMAUTHTOKEN found"}, status=400)

    tenant = bind_request_tenant(request)
    if not tenant:
        return JsonResponse({"ok": False, "error": "no tenant context"}, status=400)

    _ensure_tenant_schema(tenant)
    try:
        ta, _ = TenantApp.objects.get_or_create(
            tenant=tenant,
            app_name="mattermost",
            defaults={"status": "active"},
        )
        extra = ta.extra_config or {}
        extra["mmauthtoken"] = token
        extra["mm_session_token"] = token
        ta.extra_config = extra
        ta.save()
        return JsonResponse({"ok": True})
    except Exception as exc:
        logger.exception("store_mm_token failed")
        return JsonResponse({"ok": False, "error": str(exc)})


@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def workspace_ingest(request, endpoint_id: int):
    """Accept client-side passthrough traffic captured by the workspace shim."""
    try:
        body = request.body
        if body:
            try:
                data = json.loads(body.decode("utf-8", errors="ignore"))
            except Exception:
                data = {}
            if data:
                logger.debug("[PolySniffer] workspace_ingest from %s: %r", endpoint_id, data)
    except Exception as exc:
        logger.warning("[PolySniffer] workspace_ingest error: %s", exc)
    return JsonResponse({"ok": True})

