"""PolySniffer 2.0 — tenant binding for capture session lookup."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24
from __future__ import annotations

from dose.polysniffer.har_capture import _ensure_tenant_schema, get_active_capture_session
from dose.polysniffer.schema_patch import ensure_trafficlog_capture_columns
from dose.utils import get_current_tenant


def bind_request_tenant(request):
    """Align request.tenant with middleware search_path and session."""
    tenant = getattr(request, "tenant", None)
    if tenant:
        request.tenant = tenant
        return tenant

    from django.db import connection

    from dose.models import Tenant

    schema_name = getattr(request, "schema_name", None) or getattr(
        connection, "schema_name", None
    )
    if schema_name and schema_name != "public":
        try:
            with connection.cursor() as cur:
                cur.execute("SET LOCAL search_path TO public;")
            tenant = Tenant.objects.filter(
                schema_name=schema_name, is_active=True
            ).first()
            if tenant:
                request.tenant = tenant
                return tenant
        except Exception:
            pass

    slug = getattr(request, "current_tenant_slug", None) or request.session.get(
        "tenant_slug"
    )
    if slug:
        try:
            with connection.cursor() as cur:
                cur.execute("SET LOCAL search_path TO public;")
            tenant = Tenant.objects.filter(slug=slug, is_active=True).first()
            if tenant:
                request.tenant = tenant
                return tenant
        except Exception:
            pass

    tenant = get_current_tenant(request)
    if tenant:
        request.tenant = tenant
    return tenant


def get_sniff_capture_session(request, endpoint_host: str | None = None):
    tenant = bind_request_tenant(request)
    if tenant:
        ensure_trafficlog_capture_columns(request)
        _ensure_tenant_schema(tenant)

    if endpoint_host is not None:
        cap_id = request.session.get(f"polysniffer_{endpoint_host}_capture")
        if cap_id:
            from dose.polysniffer.models import TrafficCapture

            cap = TrafficCapture.objects.filter(pk=cap_id, is_active=True).first()
            if cap:
                return cap

    return get_active_capture_session(request)
