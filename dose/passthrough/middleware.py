# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Mattermost slug identity + SSO Town Square working — 2026-08-02 — see documentation/BINGO_MATTERMOST_SLUG_IDENTITY_SSO_WORKING_2026-08-02.md
# BINGO: Mattermost Composer via Roles Hydration — 2026-06-11 — commit 8293f54f
# BINGO: PolySniffer 2.0 Passthrough Workspace Iframe — 2026-06-24
# Certification: documentation/BINGO_MATTERMOST_COMPOSER_ROLES_2026-06-11.md
# Owner-approved 2026-08-02: /pt/admin/<slug>/ — DB PassThroughEndpoint is the only identity.
# No "trigger", no hostname-as-URL-key, no inventing upstream from the path segment.
# dose/passthrough/middleware.py - FINAL - OUT = LAST, IN = FIRST - CHIEF ARCHITECT APPROVED
import logging
import requests
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from dose.models import UserTenantMembership
from dose.passthrough.forwarding import forward_request_standardized
from dose.passthrough.registry import (
    pt_admin_core_delegated_to_urlconf,
    resolve_handler_for_endpoint,
)
from dose.passthrough.forwarding import _is_initial_page_load
from dose.utils import get_current_tenant
from dose.passthrough.incoming_path_rewrite import apply_incoming_path_rewrites

logger = logging.getLogger(__name__)


def run_pt_admin_passthrough_core(request):
    """
    Handle /pt/admin/<host>/... by loading the exact tenant PassThroughEndpoint row.

    - URL segment = endpoint.endpoint_url host
    - Upstream = the unchanged endpoint.endpoint_url from that row
    - Handler = resolve_handler_for_endpoint(endpoint)

    Returns HttpResponse, or None to let URLconf continue (static proxy, building pen).
    Caller must already enforce auth, tenant, and membership.
    """
    import sys
    print(f"\n🔥🔥🔥 [PT-CORE-ENTRY] run_pt_admin_passthrough_core - path={request.path_info}, method={request.method}", file=sys.stderr)
    sys.stderr.flush()
    path = request.path_info
    if pt_admin_core_delegated_to_urlconf(request, path):
        print(f"[PT-CORE] Delegate to URLconf (handler): {path}")
        return None
    if path.startswith("/pt/admin/passthrough/"):
        print(f"[PT-CORE] Delegate PolySniffer passthrough: {path}")
        return None
    if path.startswith("/pt/polysniff/"):
        print(f"[PT-CORE] Delegate PolySniffer pt/polysniff URLconf: {path}")
        return None

    parts = path.strip("/").split("/")
    print(f"[PT-CORE] path={path} parts={parts}")
    if len(parts) < 3 or parts[0] != "pt":
        return None
    endpoint_host = parts[2]
    print(f"[PT-CORE] endpoint_host={endpoint_host}")

    from dose.models import PassThroughEndpoint
    from urllib.parse import urlparse

    endpoint_obj = None
    try:
        for candidate in PassThroughEndpoint.objects.filter(is_enabled=True):
            if urlparse(candidate.endpoint_url or "").netloc.lower() == endpoint_host.lower():
                endpoint_obj = candidate
                break
    except Exception as e:
        print(f"[PT-CORE] Could not resolve PassThroughEndpoint by exact host: {e}")

    if endpoint_obj is None:
        print(f"[PT-CORE] No PassThroughEndpoint for host={endpoint_host!r}")
        return HttpResponse(
            f"<h2>Passthrough endpoint not found</h2>"
            f"<p>No enabled tenant PassThroughEndpoint has host <code>{endpoint_host}</code>.</p>",
            status=404,
            content_type="text/html; charset=utf-8",
        )

    endpoint = endpoint_obj
    request._passthrough_endpoint = endpoint
    print(
        f"[PT-CORE] endpoint from DB: host={endpoint_host!r} "
        f"upstream={endpoint.endpoint_url}"
    )

    handler = resolve_handler_for_endpoint(endpoint)
    print(
        f"[PT-CORE] Handler: "
        f"{handler.__class__.__name__ if handler else None}"
    )

    if handler and hasattr(handler, 'endpoint'):
        handler.endpoint = endpoint
        print("[PT-CORE] Set handler.endpoint to PassThroughEndpoint object")

    # Legacy handler argument carries the canonical host; it is not a second identity.
    trigger = endpoint_host

    # Handler hook: some paths (e.g. Mattermost /login) need try_root before upstream fetch.
    if handler and hasattr(handler, "try_root_display_shell_response"):
        early_paths = ()
        if hasattr(handler, "passthrough_early_shell_paths"):
            try:
                early_paths = tuple(handler.passthrough_early_shell_paths() or ())
            except Exception as _eps_exc:
                print(f"[PT-CORE] passthrough_early_shell_paths error: {_eps_exc}")
        if early_paths:
            import re
            _path_only = path.split("?")[0]
            _sub_match = re.match(r"^/pt/(?:admin|dose)/[^/]+(.*)$", _path_only)
            _sub = (_sub_match.group(1) if _sub_match else "") or "/"
            if not _sub.startswith("/"):
                _sub = "/" + _sub
            _norm = _sub.rstrip("/") or "/"
            _hit = _norm in {p.rstrip("/") or "/" for p in early_paths}
            if not _hit:
                for _ep in early_paths:
                    _epn = (_ep or "/").rstrip("/") or "/"
                    if _norm == _epn or _norm.startswith(_epn + "/"):
                        _hit = True
                        break
            if _hit:
                print(f"[PT-CORE] Early shell intercept for upstream subpath {_norm!r}")
                shell = handler.try_root_display_shell_response(request, endpoint, trigger)
                if shell is not None:
                    request._passthrough_handled = True
                    return shell

    print("\n" + "=" * 120)
    print("PASSTHROUGH-OUT -> SENDING TO EXTERNAL SERVICE (PT-CORE)")
    print(f"TARGET URL: {endpoint.endpoint_url}")
    print(f"PATH      : {request.path_info}")
    print(f"USER      : {request.user}")
    print("=" * 120 + "\n")

    response = forward_request_standardized(
        request, endpoint.endpoint_url, handler=handler, endpoint=endpoint, trigger=trigger
    )

    # Check if upstream service is actually down before showing a generic error page.
    # Some 502/503/504 responses are transient proxy failures while the service is healthy.
    if response.status_code in (502, 503, 504):
        service_up = False
        try:
            probe = requests.get(endpoint.endpoint_url, timeout=6, allow_redirects=True)
            service_up = probe.status_code < 500
            print(f"[PT-CORE] Health probe {endpoint.endpoint_url} -> {probe.status_code}")
        except Exception as exc:
            print(f"[PT-CORE] Health probe failed for {endpoint.endpoint_url}: {exc}")

        if not service_up:
            error_html = f"""
            <div style="padding: 40px; text-align: center;">
                <h2 style="color: #dc3545;">Service Unavailable</h2>
                <p>The external service <code>{endpoint.slug}</code> is currently not running.</p>
                <p>Status: {response.status_code}</p>
                <p><small>Endpoint: {endpoint.endpoint_url}</small></p>
            </div>
            """
            response = HttpResponse(error_html, status=503)
            print(f"[PT-CORE] Upstream service {endpoint.slug} appears down - showing error page")
        else:
            print(
                f"[PT-CORE] Upstream {endpoint.slug} returned {response.status_code}, "
                "but health probe is OK - preserving original response"
            )

    request._passthrough_handled = True
    request._passthrough_response = response
    return response


class ExternalPassthroughMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def __call__(self, request):
        """
        REQUEST PHASE - runs for every request
        This is the LAST middleware before the request leaves Django
        -> Perfect place for PASSTHROUGH-OUT
        """
        print(f"\n[PT-MW-ENTRY] __call__ - path={request.path_info}, method={request.method}")

        # Handlers may rewrite native app paths onto /pt/admin/<slug>/… (via registry hooks)
        apply_incoming_path_rewrites(request)

        # /pt/dose/<slug>/… document navigations always use the dose-home landing
        # shell (URLconf). Never admin-wrap these — that "pops out" of dose home
        # into Jazzmin. API/static under /pt/dose/ still fall through to PT core.
        if request.path_info.startswith('/pt/dose/'):
            _dose_api = (
                '/api/', '/static/', '/plugins/', '/boards/', '/calls/',
                '/bus/', '/websocket', '/files/', '/images/',
            )
            _is_dose_asset = any(p in request.path_info for p in _dose_api)
            if not _is_dose_asset:
                print(f"[PT-MW] Delegate dose-home shell to URLconf: {request.path_info}")
                return self.get_response(request)

        if request.path_info.startswith("/pt/polysniff/"):
            return self.get_response(request)

        if request.path_info.startswith("/pt/"):
            print(f"[PT-MW-TOP] ExternalPassthroughMiddleware HIT for {request.path_info}")
            user = getattr(request, "user", None)
            is_auth = user and user.is_authenticated
            print(f"[PT-MW] /pt/ hit | user={user} auth={is_auth}")
            if not is_auth:
                print("[PT-MW] BAIL: not authenticated")
                return self.get_response(request)

            tenant = get_current_tenant(request)
            print(f"[PT-MW] tenant={tenant}")
            if not tenant:
                print("[PT-MW] BAIL: no tenant")
                return self.get_response(request)
            if not request.user.is_superuser and not UserTenantMembership.objects.filter(
                user=request.user, tenant=tenant
            ).exists():
                print("[PT-MW] BAIL: not superuser and no membership")
                return self.get_response(request)

            resp = run_pt_admin_passthrough_core(request)
            if resp is not None:
                return resp

        # Not a passthrough request - continue down the stack
        return self.get_response(request)

    def process_response(self, request, response):
        """
        RESPONSE PHASE - runs for every response
        This is the FIRST middleware that sees the response coming back
        -> Perfect place for PASSTHROUGH-IN
        """
        print(f"[PT-MW-ENTRY] process_response - path={request.path_info}, status={response.status_code}")
        
        if getattr(request, '_passthrough_handled', False):
            print("\n" + "="*120)
            print("PASSTHROUGH-IN <- RESPONSE RECEIVED (FIRST ON RETURN)")
            print(f"STATUS: {response.status_code}")
            print(f"CONTENT LENGTH: {len(response.content) if hasattr(response, 'content') else 'unknown'} bytes")
            preview = response.content[:500].decode('utf-8', errors='ignore') if hasattr(response, 'content') else "No content"
            print(f"PREVIEW: {preview}")
            print("="*120 + "\n")
            try:
                from dose.passthrough.stream_debug import log_final_response_if_debug

                log_final_response_if_debug(request, response)
            except Exception as _fin_exc:
                print(f"[PT-STREAM-DEBUG] final response log error (non-blocking): {_fin_exc}")

        return response

