# dose/passthrough/middleware.py - FINAL - OUT = LAST, IN = FIRST - CHIEF ARCHITECT APPROVED
import logging
from django.utils.deprecation import MiddlewareMixin
from dose.models import UserTenantMembership
from dose.passthrough.forwarding import forward_request_standardized
from dose.passthrough.registry import (
    pt_admin_core_delegated_to_urlconf,
    resolve_handler_for_pt_admin_trigger,
)
from dose.passthrough.forwarding import _is_initial_page_load
from dose.utils import get_current_tenant
from dose.passthrough.incoming_path_rewrite import apply_incoming_path_rewrites

logger = logging.getLogger(__name__)


def run_pt_admin_passthrough_core(request):
    """
    Handle /pt/admin/<hostname>/... direct passthrough without DB lookup.
    The trigger segment IS the hostname (e.g., polysaas-odoo2.onrender.com).
    Returns HttpResponse, or None to let URLconf continue (static proxy, building pen).
    Caller must already enforce auth, tenant, and membership.
    """
    print(f"\n[PT-CORE-ENTRY] run_pt_admin_passthrough_core - path={request.path_info}, method={request.method}")
    path = request.path_info
    if pt_admin_core_delegated_to_urlconf(request, path):
        print(f"[PT-CORE] Delegate to URLconf (handler): {path}")
        return None
    if path.startswith("/pt/admin/passthrough/"):
        print(f"[PT-CORE] Delegate PolySniffer passthrough: {path}")
        return None

    parts = path.strip("/").split("/")
    print(f"[PT-CORE] path={path} parts={parts}")
    if len(parts) < 3 or parts[0] != "pt":
        return None
    trigger = parts[2]
    print(f"[PT-CORE] trigger={trigger}")

    # Fallback for when DB is unavailable (recovery scenarios)
    class SimpleEndpoint:
        def __init__(self, hostname, url=None):
            self.endpoint_url = url or f"https://{hostname}"
            self.trigger_path = hostname
            self.is_enabled = True
            self.passthrough_type = 'proxy'
            self.passthrough_stream_debug = False
            self.passthrough_log_requests = False
            self.headers_to_forward = ''
            self.description = f'Passthrough to {hostname}'

    # NOTE: We no longer look up endpoints in the DB by trigger_path.
    # Sidebar links encode the hostname directly in the URL: /pt/admin/{hostname}/
    # The hostname IS the endpoint URL — no DB lookup needed. This eliminates
    # the old two-step lookup (trigger -> DB record -> endpoint_url) entirely.
    endpoint = SimpleEndpoint(trigger)

    print(f"[PT-CORE] endpoint from URL hostname: {endpoint.endpoint_url}")

    request._passthrough_endpoint = endpoint

    handler = resolve_handler_for_pt_admin_trigger(trigger)
    print(f"[PT-CORE] Handler for {trigger}: {handler.__class__.__name__ if handler else None}")

    print("\n" + "=" * 120)
    print("PASSTHROUGH-OUT -> SENDING TO EXTERNAL SERVICE (PT-CORE)")
    print(f"TARGET URL: {endpoint.endpoint_url}")
    print(f"PATH      : {request.path_info}")
    print(f"USER      : {request.user}")
    print("=" * 120 + "\n")

    response = forward_request_standardized(
        request, endpoint.endpoint_url, handler=handler, endpoint=endpoint, trigger=trigger
    )

    # Check if upstream service is down
    if response.status_code in (502, 503, 504):
        from django.http import HttpResponse
        error_html = f"""
        <div style="padding: 40px; text-align: center;">
            <h2 style="color: #dc3545;">Service Unavailable</h2>
            <p>The external service <code>{trigger}</code> is currently not running.</p>
            <p>Status: {response.status_code}</p>
            <p><small>Endpoint: {endpoint.endpoint_url}</small></p>
        </div>
        """
        response = HttpResponse(error_html, status=503)
        print(f"[PT-CORE] Upstream service {trigger} returned {response.status_code} - showing error page")

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

        # Handlers may rewrite native app paths onto /pt/admin/<trigger>/… (via registry hooks)
        apply_incoming_path_rewrites(request)

        if request.path_info.startswith('/pt/dose/') and _is_initial_page_load(request):
            print(f"[PT-MW] Delegate landing passthrough shell to URLconf: {request.path_info}")
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