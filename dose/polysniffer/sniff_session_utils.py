"""PolySniffer capture session helpers (non-frozen companion to sniff_session.py)."""
from __future__ import annotations

from django.utils import timezone

from dose.polysniffer.har_capture import _ensure_tenant_schema
from dose.polysniffer.models import TrafficCapture
from dose.polysniffer.schema_patch import ensure_trafficlog_capture_columns
from dose.polysniffer.sniff_tenant import bind_request_tenant, get_sniff_capture_session
from dose.utils import get_current_tenant


def _session_name(endpoint_id: int, mode: str) -> str:
    ts = timezone.now().strftime("%Y%m%d-%H%M")
    safe_mode = mode if mode in ("native", "passthrough") else "native"
    return f"ep{endpoint_id}-{safe_mode}-{ts}"


def ensure_capture_session(request, endpoint_id: int, mode: str) -> TrafficCapture | None:
    """
    Start or switch capture session for workspace mode URLs.

    Visiting /workspace/native/ or /workspace/passthrough/ must not depend on
    client-side fetch + redirect ( brittle in cached shells ).
    """
    mode = (mode or "").strip().lower()
    if mode not in ("native", "passthrough"):
        return None

    tenant = bind_request_tenant(request) or get_current_tenant(request)
    if not tenant:
        return None

    ensure_trafficlog_capture_columns(request)
    _ensure_tenant_schema(tenant)

    existing = get_sniff_capture_session(request, endpoint_id)
    session_mode = (request.session.get(f"polysniffer_ep{endpoint_id}_mode") or "").strip().lower()
    if existing and session_mode == mode:
        return existing

    TrafficCapture.objects.filter(tenant=tenant, is_active=True).update(is_active=False)
    cap = TrafficCapture.objects.create(
        tenant=tenant,
        capture_name=_session_name(endpoint_id, mode),
        description=f"PolySniffer 2.0 {mode} endpoint_id={endpoint_id}",
        is_active=True,
    )
    request.session[f"polysniffer_ep{endpoint_id}_mode"] = mode
    request.session[f"polysniffer_ep{endpoint_id}_capture_id"] = cap.id
    request.session.modified = True
    return cap
