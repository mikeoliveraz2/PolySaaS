"""PolySniffer 2.0 — capture session start/stop in the tenant schema."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24
from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from dose.polysniffer.har_capture import _ensure_tenant_schema
from dose.polysniffer.models import TrafficCapture
from dose.polysniffer.schema_patch import ensure_trafficlog_capture_columns
from dose.polysniffer.sniff_tenant import bind_request_tenant
from dose.utils import get_current_tenant


def _session_name(endpoint_id: int, mode: str) -> str:
    ts = timezone.now().strftime("%Y%m%d-%H%M")
    safe_mode = mode if mode in ("native", "passthrough") else "native"
    return f"ep{endpoint_id}-{safe_mode}-{ts}"


@staff_member_required
@require_http_methods(["POST"])
def session_start(request, endpoint_id: int):
    mode = (request.POST.get("mode") or "native").strip().lower()
    if mode not in ("native", "passthrough"):
        return JsonResponse({"error": "mode must be native or passthrough"}, status=400)

    tenant = bind_request_tenant(request) or get_current_tenant(request)
    if not tenant:
        return JsonResponse({"error": "no tenant context"}, status=400)

    ensure_trafficlog_capture_columns(request)
    _ensure_tenant_schema(tenant)

    TrafficCapture.objects.filter(tenant=tenant, is_active=True).update(is_active=False)
    cap = TrafficCapture.objects.create(
        tenant=tenant,
        capture_name=_session_name(endpoint_id, mode),
        description=f"PolySniffer 2.0 {mode} endpoint_id={endpoint_id}",
        is_active=True,
    )
    request.session[f"polysniffer_ep{endpoint_id}_mode"] = mode
    request.session[f"polysniffer_ep{endpoint_id}_capture_id"] = cap.id
    return JsonResponse(
        {
            "ok": True,
            "capture_id": cap.id,
            "capture_name": cap.capture_name,
            "mode": mode,
        }
    )


@staff_member_required
@require_http_methods(["POST"])
def session_stop(request, endpoint_id: int):
    tenant = bind_request_tenant(request) or get_current_tenant(request)
    if not tenant:
        return JsonResponse({"error": "no tenant context"}, status=400)

    _ensure_tenant_schema(tenant)
    updated = TrafficCapture.objects.filter(tenant=tenant, is_active=True).update(is_active=False)
    request.session.pop(f"polysniffer_ep{endpoint_id}_capture_id", None)
    request.session.pop(f"polysniffer_ep{endpoint_id}_mode", None)
    return JsonResponse({"ok": True, "stopped": updated})
