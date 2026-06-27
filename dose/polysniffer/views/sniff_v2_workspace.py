"""
PolySniffer 2.0 — split workspace.

Native and passthrough browse render inline in the left pane (admin-style div embed).
Only the live capture panel uses an iframe on the right.
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24
# BINGO: PolySniffer 2.0 Passthrough Workspace Iframe — 2026-06-24
from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from dose.polysniffer.har_capture import _ensure_tenant_schema, log_http_exchange
from dose.polysniffer.sniff_forward import forward_sniff_native
from dose.polysniffer.sniff_native_embed import (
    build_inline_native_embed_context,
    workspace_browse_prefix,
    workspace_shell_prefix,
    wrap_native_sniff_for_workspace,
)
from dose.polysniffer.handler_hooks import path_looks_like_non_page, workspace_browse_subpath
from dose.polysniffer.sniff_pt_embed import build_inline_passthrough_embed_context
from dose.polysniffer.workspace_pt_redirect import workspace_redirect_for_pt_response
from dose.polysniffer.sniff_tenant import bind_request_tenant, get_sniff_capture_session
from dose.polysniffer.models import TrafficLog
from dose.polysniffer.schema_patch import ensure_trafficlog_capture_columns
from dose.polysniffer.views.core import get_endpoint_any_schema


def _endpoint_label(endpoint) -> str:
    return endpoint.menu_title or endpoint.endpoint_url or f"Endpoint {endpoint.pk}"


def _session_mode(request, endpoint_id: int) -> str:
    mode = (request.session.get(f"polysniffer_ep{endpoint_id}_mode") or "").strip().lower()
    return mode if mode in ("native", "passthrough") else ""


def _resolve_pt_handler(endpoint):
    from urllib.parse import urlparse

    from dose.passthrough.registry import resolve_handler_for_pt_admin_trigger

    trigger = urlparse((getattr(endpoint, "endpoint_url", None) or "").strip()).netloc
    if not trigger:
        return None, ""
    handler = resolve_handler_for_pt_admin_trigger(trigger)
    if handler is not None:
        handler.endpoint = endpoint
    return handler, trigger


def _browse_subpath(endpoint, handler=None, request=None) -> str:
    """Workspace sniff embed entry path — session landing or global handler entry."""
    return workspace_browse_subpath(handler, endpoint, request=request)


def _is_forward_only_browse_path(path: str, handler=None, request=None) -> bool:
    raw = (path or "").strip()
    if not raw:
        return False
    if raw.lower().startswith("browse/") or raw.lower() == "browse":
        return True
    return path_looks_like_non_page(raw, handler=handler, request=request)


def _workspace_browse_redirect_path(browse_subpath: str) -> str:
    """Preserve trailing slash (HubSpot expects /login/ not /login)."""
    sub = (browse_subpath or "").strip()
    if sub.startswith("/"):
        sub = sub[1:]
    if (browse_subpath or "").rstrip().endswith("/") and sub and not sub.endswith("/"):
        sub = sub + "/"
    return sub


@staff_member_required
def sniff_shell(request, endpoint_id: int, mode: str | None = None, browse_path: str = ""):
    """PolySniffer workspace — native inline embed or passthrough orchestration + capture."""
    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception as exc:
        return render(
            request,
            "polysniffer/sniff_workspace.html",
            {"error": str(exc), "endpoint_id": endpoint_id},
            status=404,
        )

    active_mode = (mode or _session_mode(request, endpoint_id)).strip().lower()
    if mode in ("native", "passthrough"):
        from dose.polysniffer.sniff_session_utils import ensure_capture_session

        ensure_capture_session(request, endpoint_id, mode)
        active_mode = mode
    elif active_mode not in ("native", "passthrough"):
        active_mode = ""

    upstream_url = (getattr(endpoint, "endpoint_url", None) or "").strip().rstrip("/")
    pt_handler, _pt_trigger = _resolve_pt_handler(endpoint)
    browse_subpath = _browse_subpath(endpoint, pt_handler, request)
    upstream_browse_url = f"{upstream_url}{browse_subpath}" if upstream_url else ""
    active_session = get_sniff_capture_session(request, endpoint_id)

    passthrough_browse_url = ""
    native_shell_url = ""
    native_inline = None
    native_inline_error = ""
    passthrough_inline = None
    passthrough_inline_error = ""
    if active_session and active_mode == "native":
        inline_subpath = (browse_path or "").strip().strip("/")
        if not inline_subpath:
            return redirect(f"{workspace_shell_prefix(endpoint_id)}/{_workspace_browse_redirect_path(browse_subpath)}")
        native_shell_url = f"{workspace_shell_prefix(endpoint_id)}/{inline_subpath}"
        native_inline = build_inline_native_embed_context(
            request,
            endpoint_id,
            endpoint,
            inline_subpath,
            endpoint_label=_endpoint_label(endpoint),
        )
        if native_inline is None:
            native_inline_error = (
                f"Could not load native inline content for /{inline_subpath}. "
                "Check endpoint URL and try again."
            )
    elif active_session and active_mode == "passthrough":
        inline_subpath = (browse_path or "").strip().strip("/")
        if not inline_subpath:
            return redirect(f"{workspace_shell_prefix(endpoint_id)}/{_workspace_browse_redirect_path(browse_subpath)}")
        pt_ctx = build_inline_passthrough_embed_context(
            request,
            endpoint_id,
            endpoint,
            inline_subpath,
            endpoint_label=_endpoint_label(endpoint),
        )
        if pt_ctx and pt_ctx.get("redirect"):
            return redirect(pt_ctx["redirect"])
        if pt_ctx:
            passthrough_inline = pt_ctx
        else:
            passthrough_inline_error = (
                f"Could not load passthrough inline content for /{inline_subpath}. "
                "Check endpoint URL and try again."
            )

    capture_frame_url = f"/dose/sniff/{endpoint_id}/workspace/capture/"
    if active_mode in ("native", "passthrough"):
        capture_frame_url = f"{capture_frame_url}?mode={active_mode}"

    return render(
        request,
        "polysniffer/sniff_workspace.html",
        {
            "endpoint": endpoint,
            "endpoint_id": endpoint_id,
            "endpoint_label": _endpoint_label(endpoint),
            "mode": active_mode,
            "passthrough_browse_url": passthrough_browse_url,
            "passthrough_inline": passthrough_inline,
            "passthrough_inline_error": passthrough_inline_error,
            "native_shell_url": native_shell_url,
            "native_inline": native_inline,
            "native_inline_error": native_inline_error,
            "browse_subpath": browse_subpath,
            "upstream_browse_url": upstream_browse_url,
            "active_session": active_session,
            "diff_url": f"/dose/sniff/{endpoint_id}/diff/",
            "export_url": f"/dose/sniff/{endpoint_id}/export-har/",
            "capture_frame_url": capture_frame_url,
        },
    )


# Alias kept for older links
sniff_workspace = sniff_shell


@staff_member_required
def workspace_dispatch(request, endpoint_id: int, browse_path: str = ""):
    """Route HTML page navigations to the shell; API/assets to the sniff proxy."""
    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception:
        endpoint = None
    handler, _trigger = _resolve_pt_handler(endpoint) if endpoint else (None, "")
    mode = _session_mode(request, endpoint_id)
    if request.method != "GET" or _is_forward_only_browse_path(browse_path, handler=handler, request=request):
        if mode == "passthrough":
            return workspace_pt_browse(request, endpoint_id, path=browse_path)
        return workspace_browse(request, endpoint_id, path=browse_path)
    return sniff_shell(request, endpoint_id, browse_path=browse_path)


@staff_member_required
@xframe_options_exempt
@csrf_exempt
def workspace_pt_proxy(request, endpoint_id: int, path: str = ""):
    """Forms/login via /pt/polysniff/ dispatch; return to workspace shell."""
    if not request.user.is_staff:
        return HttpResponseForbidden("Staff only")
    from urllib.parse import urlparse

    from dose.polysniffer.sniff_pt_proxy import dispatch_polysniff_passthrough

    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception as exc:
        return HttpResponseForbidden(str(exc))

    trigger = urlparse((endpoint.endpoint_url or "").strip()).netloc
    handler, _ = _resolve_pt_handler(endpoint)

    response = dispatch_polysniff_passthrough(request, endpoint_id, path or "")
    wrapped = workspace_redirect_for_pt_response(
        request, endpoint_id, path, response, trigger=trigger, handler=handler,
    )
    return wrapped if wrapped is not None else response


@staff_member_required
@xframe_options_exempt
@csrf_exempt
def workspace_pt_browse(request, endpoint_id: int, path: str = ""):
    """Passthrough API/assets via /pt/polysniff/ dispatch."""
    if not request.user.is_staff:
        return HttpResponseForbidden("Staff only")
    from dose.polysniffer.sniff_pt_proxy import dispatch_polysniff_passthrough

    try:
        get_endpoint_any_schema(endpoint_id, request)
    except Exception as exc:
        return HttpResponseForbidden(str(exc))

    return dispatch_polysniff_passthrough(request, endpoint_id, path or "")


@staff_member_required
@xframe_options_exempt
@csrf_exempt
def workspace_browse(request, endpoint_id: int, path: str = ""):
    """Native sniff transparent proxy (API/assets) — optional standalone embed document."""
    if not request.user.is_staff:
        return HttpResponseForbidden("Staff only")
    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception as exc:
        return HttpResponseForbidden(str(exc))

    request._polysniffer_endpoint_id = endpoint_id
    request._polysniffer_sniff_mode = "native"
    bind_request_tenant(request)
    session = get_sniff_capture_session(request, endpoint_id)
    if session:
        request._polysniffer_capture = session

    response = forward_sniff_native(request, endpoint, path)
    return wrap_native_sniff_for_workspace(
        request,
        endpoint_id,
        response,
        endpoint_label=_endpoint_label(endpoint),
    )


@staff_member_required
@xframe_options_exempt
def workspace_capture_frame(request, endpoint_id: int):
    """Green-screen capture panel for the right iframe."""
    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception as exc:
        return render(
            request,
            "polysniffer/sniff_workspace_capture.html",
            {"error": str(exc), "endpoint_id": endpoint_id},
            status=404,
        )

    active_session = get_sniff_capture_session(request, endpoint_id)
    mode = (request.GET.get("mode") or _session_mode(request, endpoint_id) or "native").strip().lower()
    if mode not in ("native", "passthrough"):
        mode = "native"

    return render(
        request,
        "polysniffer/sniff_workspace_capture.html",
        {
            "endpoint_id": endpoint_id,
            "endpoint_label": _endpoint_label(endpoint),
            "active_session": active_session,
            "mode": mode,
            "poll_url": f"/dose/sniff/{endpoint_id}/workspace/poll/",
        },
    )


@staff_member_required
@require_GET
def workspace_poll(request, endpoint_id: int):
    tenant = bind_request_tenant(request)
    if not tenant:
        return JsonResponse({"success": False, "error": "no tenant context"}, status=400)

    ensure_trafficlog_capture_columns(request)
    _ensure_tenant_schema(tenant)

    mode = (request.GET.get("mode") or _session_mode(request, endpoint_id) or "native").strip().lower()
    if mode not in ("native", "passthrough"):
        mode = "native"

    try:
        since_id = int(request.GET.get("since_id", 0))
    except (TypeError, ValueError):
        since_id = 0

    session = get_sniff_capture_session(request, endpoint_id)
    qs = TrafficLog.objects.all()
    if session:
        qs = qs.filter(capture_session=session)
    else:
        if mode == "passthrough":
            qs = qs.filter(client_path__contains=f"/pt/polysniff/{endpoint_id}")
        else:
            qs = qs.filter(client_path__contains=f"/sniff/{endpoint_id}/workspace")

    qs = qs.filter(capture_source=mode)
    if since_id:
        qs = qs.filter(id__gt=since_id)
        logs = list(qs.order_by("id")[:100])
    else:
        # Initial backfill: newest rows first in UI (client prepends in id order).
        logs = list(qs.order_by("-id")[:100])
        logs.reverse()

    try:
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
            }
            for log in logs
        ]
    except Exception as exc:
        return JsonResponse(
            {
                "success": True,
                "captures": [],
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
            "session_active": bool(session),
            "session_name": session.capture_name if session else "",
            "mode": mode,
        }
    )


@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def workspace_ingest(request, endpoint_id: int):
    """Accept client-side fetch/XHR logs from browse tab or passthrough iframe."""
    import json
    import traceback
    import logging

    logger = logging.getLogger(__name__)

    tenant = bind_request_tenant(request)
    if not tenant:
        return JsonResponse({"ok": False, "error": "no tenant context"}, status=400)

    session = get_sniff_capture_session(request, endpoint_id)
    if not session:
        return JsonResponse({"ok": False, "error": "no active capture session"}, status=400)

    ensure_trafficlog_capture_columns(request)
    _ensure_tenant_schema(tenant)

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

    method = (data.get("method") or "GET").upper()[:10]
    url = (data.get("url") or "")[:500]
    path = (data.get("path") or url)[:500]
    status_code = int(data.get("status_code") or 0)
    duration_ms = float(data.get("duration_ms") or 0)

    mode = (_session_mode(request, endpoint_id) or "native").strip().lower()
    if mode not in ("native", "passthrough"):
        mode = "native"

    try:
        row_id = log_http_exchange(
            request,
            method=method,
            url=url,
            path=path,
            client_path=path,
            capture_source=mode,
            headers={},
            cookies={},
            query_params={},
            body="",
            status_code=status_code,
            response_headers={},
            response_body="",
            response_size=0,
            duration_ms=duration_ms,
            endpoint_name=f"ep{endpoint_id}",
            service="client",
            capture_session=session,
            sniff_mode=mode,
        )
        return JsonResponse({"ok": True, "id": row_id})
    except Exception as e:
        logger.error(f"workspace_ingest error: {e}\n{traceback.format_exc()}")
        return JsonResponse(
            {
                "ok": False,
                "error": f"log_http_exchange failed: {str(e)}",
                "traceback": traceback.format_exc(),
            },
            status=500,
        )
