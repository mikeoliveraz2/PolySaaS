# dose/passthrough/middleware.py — FINAL — OUT = LAST, IN = FIRST — CHIEF ARCHITECT APPROVED
import logging
from django.utils.deprecation import MiddlewareMixin
from dose.models import UserTenantMembership
from dose.passthrough.forwarding import forward_request_standardized
from dose.passthrough.handlers.registry import (
    get_handler_for_endpoint,
    pt_admin_core_delegated_to_urlconf,
)
from dose.passthrough.incoming_path_rewrite import apply_incoming_path_rewrites
from dose.utils import get_current_tenant

logger = logging.getLogger(__name__)


def _is_initial_page_load(request):
    """
    Detect if this is an initial page load (browser navigation) vs API/asset request.
    Initial page loads should be wrapped in the admin template for embedded display.
    """
    # XHR/fetch requests are NOT initial page loads
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return False
    
    # Check Accept header - browsers send text/html for navigation
    accept = request.headers.get('Accept', '')
    if 'text/html' not in accept:
        return False
    
    # Check if path has a file extension (static assets)
    path = request.path_info
    if '.' in path.split('/')[-1]:
        ext = path.split('.')[-1].lower()
        if ext in ('js', 'css', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'ico', 'woff', 'woff2', 'ttf', 'eot', 'map'):
            return False
    
    # API paths are not initial page loads
    api_prefixes = ('/api/', '/plugins/', '/boards/', '/calls/', '/bus/', '/websocket')
    for prefix in api_prefixes:
        if prefix in path:
            return False
    
    return True


def _extract_head_and_body(html):
    """
    Extract <head> content and <body> content from a full HTML document.
    Returns (head_content, body_content) tuple.
    """
    import re
    
    head_content = ''
    body_content = html
    
    # Extract content between <head> and </head>
    head_match = re.search(r'<head[^>]*>(.*?)</head>', html, re.DOTALL | re.IGNORECASE)
    if head_match:
        head_content = head_match.group(1)
    
    # Extract content between <body> and </body>
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
    if body_match:
        body_content = body_match.group(1)
    elif '<body' in html.lower():
        # Body tag exists but no closing - take everything after <body>
        body_start = re.search(r'<body[^>]*>', html, re.IGNORECASE)
        if body_start:
            body_content = html[body_start.end():]
            # Remove closing </html> if present
            body_content = re.sub(r'</html>\s*$', '', body_content, flags=re.IGNORECASE)
    
    return head_content, body_content


def _wrap_in_admin_template(request, response, trigger, endpoint):
    """
    Wrap the raw proxied HTML response in the admin template for embedded display.
    This gives us the PolySaaS sidebar, header, and proper layout.
    
    The upstream HTML is a full document (<html><head>...</head><body>...</body></html>).
    We extract the <head> content (styles, scripts, shims) and <body> content separately,
    then inject them into the appropriate blocks of the admin template.
    """
    from django.template.loader import render_to_string
    from django.http import HttpResponse as DjangoHttpResponse
    from django.utils.safestring import mark_safe
    
    # Only wrap HTML responses
    content_type = response.get('Content-Type', '')
    if 'text/html' not in content_type:
        return response
    
    # Get the raw HTML content
    try:
        raw_html = response.content.decode('utf-8', errors='ignore')
    except Exception:
        return response
    
    # Don't wrap if it's an error page or empty
    if not raw_html or len(raw_html) < 100:
        return response
    
    norm = trigger.strip('/').lower().split('/')[-1].replace('-', '_')
    embed_title = norm.replace('_', ' ').title()
    embed_src = f'/pt/admin/{norm}/'
    
    # Extract head and body from the upstream HTML document
    head_content, body_content = _extract_head_and_body(raw_html)
    
    # The body content goes in the scope div
    # The head content (styles, scripts, shims) goes in embed_head for extrahead block
    embed_body = mark_safe(
        f'<div class="polysaas-passthrough-scope" data-polysaas-embed-trigger="{norm}">'
        f'{body_content}</div>'
    )
    embed_head = mark_safe(head_content)
    
    try:
        wrapped_html = render_to_string(
            'admin/passthrough_embed.html',
            {
                'embed_src': embed_src,
                'embed_title': embed_title,
                'embed_head': embed_head,
                'embed_body': embed_body,
            },
            request=request,
        )
        
        wrapped_response = DjangoHttpResponse(wrapped_html, status=response.status_code)
        wrapped_response['Content-Type'] = 'text/html; charset=utf-8'
        wrapped_response['X-Frame-Options'] = 'ALLOWALL'
        wrapped_response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        # Copy cookies from original response
        for cookie_name in response.cookies:
            wrapped_response.cookies[cookie_name] = response.cookies[cookie_name].value
            wrapped_response.cookies[cookie_name]['path'] = response.cookies[cookie_name].get('path', '/')
            wrapped_response.cookies[cookie_name]['samesite'] = 'Lax'
        
        print(f"[PT-MW] Wrapped response in admin template for {norm} (head={len(head_content)} body={len(body_content)} chars)")
        return wrapped_response
    except Exception as exc:
        print(f"[PT-MW] Failed to wrap in admin template: {exc}")
        import traceback
        traceback.print_exc()
        return response


def run_pt_admin_passthrough_core(request):
    """
    Handle /pt/admin/<hostname>/... direct passthrough without DB lookup.
    The trigger segment IS the hostname (e.g., polysaas-odoo2.onrender.com).
    Returns HttpResponse, or None to let URLconf continue (static proxy, building pen).
    Caller must already enforce auth, tenant, and membership.
    """
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

    # PICOLLO PASSO: Direct URL passthrough - trigger IS the hostname
    # e.g., trigger = "polysaas-odoo2.onrender.com" -> endpoint_url = "https://polysaas-odoo2.onrender.com"
    class SimpleEndpoint:
        def __init__(self, hostname):
            self.endpoint_url = f"https://{hostname}"
            self.trigger_path = hostname
            self.is_enabled = True
            self.passthrough_type = 'proxy'
            # Minimal attrs for handler compatibility
            self.passthrough_stream_debug = False
            self.passthrough_log_requests = False
            self.headers_to_forward = ''
            self.description = f'Passthrough to {hostname}'
    
    endpoint = SimpleEndpoint(trigger)
    print(f"[PT-CORE] SimpleEndpoint created: {endpoint.endpoint_url}")
    request._passthrough_endpoint = endpoint

    # PICOLLO PASSO: Direct handler selection by hostname - avoids DB-dependent registry lookup
    trigger_lower = trigger.lower()
    handler = None
    if 'odoo' in trigger_lower:
        from dose.passthrough.handlers.odoo_handler import OdooPassthroughHandler
        handler = OdooPassthroughHandler()
        print(f"[PT-CORE] Selected OdooPassthroughHandler for {trigger}")
    elif 'mattermost' in trigger_lower:
        from dose.passthrough.handlers.mattermost_handler import MattermostPassthroughHandler
        handler = MattermostPassthroughHandler()
        print(f"[PT-CORE] Selected MattermostPassthroughHandler for {trigger}")
    elif 'nextcloud' in trigger_lower:
        from dose.passthrough.handlers.nextcloud_handler import NextcloudPassthroughHandler
        handler = NextcloudPassthroughHandler()
        print(f"[PT-CORE] Selected NextcloudPassthroughHandler for {trigger}")
    else:
        # Fallback to registry for unknown hostnames
        handler = get_handler_for_endpoint(endpoint, request)
        print(f"[PT-CORE] Fallback registry handler for {trigger}: {handler}")

    try_root = (
        getattr(handler, "try_root_display_shell_response", None)
        if handler is not None
        else None
    )
    if callable(try_root):
        shell = try_root(request, endpoint, trigger)
        if shell is not None:
            print("[PT-CORE] Handler display shell — admin/display.html (no forward)")
            request._passthrough_handled = True
            request._passthrough_response = shell
            return shell

    print("\n" + "=" * 120)
    print("PASSTHROUGH-OUT -> SENDING TO EXTERNAL SERVICE (PT-CORE)")
    print(f"TARGET URL: {endpoint.endpoint_url}")
    print(f"PATH      : {request.path_info}")
    print(f"USER      : {request.user}")
    print("=" * 120 + "\n")

    response = forward_request_standardized(
        request, endpoint.endpoint_url, handler=handler, endpoint=endpoint
    )

    if _is_initial_page_load(request):
        print("[PT-CORE] Initial page load — wrapping in admin template")
        response = _wrap_in_admin_template(request, response, trigger, endpoint)
    else:
        print("[PT-CORE] API/asset — raw response")

    request._passthrough_handled = True
    request._passthrough_response = response
    return response


class ExternalPassthroughMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def __call__(self, request):
        """
        REQUEST PHASE — runs for every request
        This is the LAST middleware before the request leaves Django
        -> Perfect place for PASSTHROUGH-OUT
        """
        # Handlers may rewrite native app paths onto /pt/admin/<trigger>/… (see incoming_path_rewrite).
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

        # Not a passthrough request — continue down the stack
        return self.get_response(request)

    def process_response(self, request, response):
        """
        RESPONSE PHASE — runs for every response
        This is the FIRST middleware that sees the response coming back
        -> Perfect place for PASSTHROUGH-IN
        """
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