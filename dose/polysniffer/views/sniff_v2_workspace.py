"""Admin-only PolySniffer control screen with top-level browser launches."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24
from __future__ import annotations

import json
import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from dose.polysniffer.har_capture import _ensure_tenant_schema
from dose.polysniffer.sniff_tenant import bind_request_tenant, get_sniff_capture_session
from dose.polysniffer.models import TrafficLog
from dose.polysniffer.schema_patch import ensure_trafficlog_capture_columns
from dose.models import TenantApp
from dose.polysniffer.views.core import get_endpoint_by_host


def _workspace_pt_shell_base(endpoint_host: str, endpoint_id: int) -> str:
    """URL prefix for passthrough workspace navigation — matches sniff_urls.py."""
    return f"/admin/polysniffer/sniff/{endpoint_host}/workspace/passthrough"

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


@staff_member_required
def sniff_shell(request, endpoint_host: str, mode: str | None = None, browse_path: str = ""):
    """PolySniffer workspace — native inline embed or passthrough orchestration + capture."""
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
        # Fresh workspace window: do not carry over a prior capture session
        request.session.pop(f"polysniffer_{endpoint_host}_capture", None)
        request.session.pop(f"polysniffer_{endpoint_host}_mode", None)
        active_mode = ""
    request.session.modified = True

    upstream_url = (getattr(endpoint, "endpoint_url", None) or "").strip().rstrip("/")
    browse_subpath = _native_browse_subpath(endpoint)
    upstream_browse_url = f"{upstream_url}{browse_subpath}" if upstream_url else ""
    active_session = get_sniff_capture_session(request, endpoint_host) if active_mode else None

    app_launch_url = ""
    pt_embed_ctx = None
    if active_session and active_mode == "native":
        app_launch_url = upstream_browse_url
    elif active_session and active_mode == "passthrough":
        frame_subpath = (browse_path or browse_subpath or "/").strip()
        if not frame_subpath.startswith("/"):
            frame_subpath = f"/{frame_subpath}"
        app_launch_url = (
            f"{endpoint.get_proxy_prefix().rstrip('/')}"
            f"{frame_subpath}"
        )
        # Build the inline HTML scoping for non-iframe passthrough.
        try:
            from dose.polysniffer.sniff_pt_embed import build_inline_passthrough_embed_context

            pt_embed_ctx = build_inline_passthrough_embed_context(
                request,
                endpoint.pk,
                endpoint,
                frame_subpath,
                endpoint_label=_endpoint_label(endpoint),
                shell_base=_workspace_pt_shell_base(endpoint_host, endpoint.pk),
            )
        except Exception as exc:
            logger.exception("passthrough inline embed build failed")
    workspace_prefix = f"/admin/polysniffer/sniff/{endpoint_host}"
    poll_url = f"{workspace_prefix}/workspace/poll/"

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
    }
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

        ensure_trafficlog_capture_columns(request)
        _ensure_tenant_schema(tenant)

        mode = (request.GET.get("mode") or _session_mode(request, endpoint_host) or "native").strip().lower()
        if mode not in ("native", "passthrough"):
            mode = "native"

        try:
            since_id = int(request.GET.get("since_id", 0))
        except (TypeError, ValueError):
            since_id = 0

        session = get_sniff_capture_session(request, endpoint_host)
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
    except Exception as exc:
        logger.exception("workspace_poll failed")
        return JsonResponse(
            {
                "success": True,
                "captures": [],
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

