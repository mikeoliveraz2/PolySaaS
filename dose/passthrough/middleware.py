# dose/passthrough/middleware.py — FINAL — OUT = LAST, IN = FIRST — CHIEF ARCHITECT APPROVED
import logging
from django.utils.deprecation import MiddlewareMixin
from dose.models import PassThroughEndpoint, UserTenantMembership
from dose.passthrough.forwarding import forward_request_standardized
from dose.passthrough.handlers.registry import get_handler_for_endpoint
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

            parts = request.path_info.strip("/").split("/")
            print(f"[PT-MIDDLEWARE] path={request.path_info} parts={parts}")
            if len(parts) >= 3 and parts[0] == "pt":
                trigger = parts[2]
                print(f"[PT-MIDDLEWARE] trigger={trigger}")

                endpoint = PassThroughEndpoint.objects.filter(
                    trigger_path__iexact=trigger,
                    is_enabled=True
                ).first()
                print(f"[PT-MIDDLEWARE] endpoint={endpoint}")

                if endpoint:
                    print("\n" + "="*120)
                    print("PASSTHROUGH-OUT -> SENDING TO EXTERNAL SERVICE (LAST BEFORE EXIT)")
                    print(f"TARGET URL: {endpoint.endpoint_url}")
                    print(f"PATH      : {request.path_info}")
                    print(f"USER      : {request.user}")
                    print("="*120 + "\n")

                    handler = get_handler_for_endpoint(endpoint, request)
                    response = forward_request_standardized(request, endpoint.endpoint_url, handler=handler)

                    # For initial page loads, wrap the response in the admin template
                    # so Mattermost/Odoo/etc display embedded with PolySaaS sidebar
                    if _is_initial_page_load(request):
                        print(f"[PT-MW] Initial page load detected — wrapping in admin template")
                        response = _wrap_in_admin_template(request, response, trigger, endpoint)
                    else:
                        print(f"[PT-MW] API/asset request — returning raw response")

                    # Mark so process_response knows it was us
                    request._passthrough_handled = True
                    request._passthrough_response = response

                    return response  # SHORT-CIRCUIT — WE ARE DONE

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

        return response