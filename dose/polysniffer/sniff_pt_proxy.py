"""
PolySniffer passthrough — public /pt/polysniff/{endpoint_id}/ routes.

Production handlers still run on internal /pt/admin/{trigger}/ paths; responses
are rewritten so redirects and shim PROXY_PREFIX stay on /pt/polysniff/ (iframe-safe).
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Passthrough Workspace Iframe — 2026-06-24
from __future__ import annotations

from urllib.parse import urlparse

from django.http import HttpResponse


def public_polysniff_prefix(endpoint_id: int) -> str:
    return f"/pt/polysniff/{endpoint_id}"


def legacy_sniff_prefix(endpoint_id: int) -> str:
    return f"/dose/sniff/{endpoint_id}/passthrough"


def admin_prefix(trigger: str) -> str:
    return f"/pt/admin/{trigger}"


def internal_admin_path(trigger: str, subpath: str) -> str:
    sub = subpath or ""
    if sub and not sub.startswith("/"):
        sub = "/" + sub
    return f"{admin_prefix(trigger)}{sub}"


def _endpoint_trigger(endpoint) -> str:
    raw = (endpoint.endpoint_url or "").strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return urlparse(raw).netloc
    return raw.split("/")[0]


def rewrite_polysniff_response(response, *, endpoint_id: int, trigger: str, public_prefix: str):
    """Keep browser navigation on the PolySniffer public prefix (not /pt/admin/)."""
    admin_pf = admin_prefix(trigger)
    replacements = (
        (admin_pf, public_prefix),
        (legacy_sniff_prefix(endpoint_id), public_prefix),
    )

    location = response.get("Location")
    if location:
        for old, new in replacements:
            if location.startswith(old):
                response["Location"] = new + location[len(old) :]
                break

    content_type = (response.get("Content-Type") or "").lower()
    if hasattr(response, "content") and response.content and "text/html" in content_type:
        body = response.content.decode("utf-8", errors="ignore")
        for old, new in replacements:
            body = body.replace(old, new)
        response.content = body.encode("utf-8")
        if "Content-Length" in response:
            response["Content-Length"] = len(response.content)

    response.xframe_options_exempt = True
    return response


def dispatch_polysniff_passthrough(request, endpoint_id: int, path: str = "", *, public_prefix: str | None = None):
    from dose.polysniffer.har_capture import get_active_capture_session
    from dose.polysniffer.views.core import get_endpoint_any_schema

    if not request.user.is_staff:
        from django.http import HttpResponseForbidden

        return HttpResponseForbidden("Staff only")

    endpoint = get_endpoint_any_schema(endpoint_id, request)
    trigger = _endpoint_trigger(endpoint)
    subpath = path or ""
    if subpath and not subpath.startswith("/"):
        subpath = "/" + subpath

    pub = (public_prefix or public_polysniff_prefix(endpoint_id)).rstrip("/")
    request._polysniffer_endpoint_id = endpoint_id
    request._polysniffer_sniff_mode = "passthrough"
    request._polysniffer_proxy_prefix = pub
    cap = get_active_capture_session(request, endpoint_id)
    if cap:
        request._polysniffer_capture = cap

    admin_path = internal_admin_path(trigger, subpath)
    request.path_info = admin_path
    request.path = admin_path
    request.META["PATH_INFO"] = admin_path
    request._polysniffer_client_path = f"{pub}{subpath or '/'}"

    from dose.admin_views import pt_admin_generic_passthrough_view

    response = pt_admin_generic_passthrough_view(
        request,
        endpoint=trigger,
        subpath=subpath.lstrip("/") or None,
    )
    return rewrite_polysniff_response(
        response,
        endpoint_id=endpoint_id,
        trigger=trigger,
        public_prefix=pub,
    )
