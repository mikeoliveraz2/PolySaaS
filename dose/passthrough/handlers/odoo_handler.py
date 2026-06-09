# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Odoo Passthrough Layout Fix — 2026-06-09

import logging
import re
from django.http import HttpResponse
from dose.passthrough.handlers.handler_base import PassthroughHandlerBase

logger = logging.getLogger(__name__)

VERSION = "ODOO_HANDLER_v20260608_1330_MINIMAL"
print(f"[ODOO HANDLER] {VERSION} LOADED")


class OdooPassthroughHandler(PassthroughHandlerBase):
    """Clean and minimal Odoo passthrough handler with proper inheritance."""

    @classmethod
    def matches_endpoint(cls, endpoint) -> bool:
        """Discover Odoo endpoints by hostname."""
        url = (getattr(endpoint, 'endpoint_url', '') or '').lower()
        return 'odoo' in url

    def needs_readable_response_body(self, request, target_url: str) -> bool:
        """We need readable body to rewrite asset URLs."""
        return True

    def should_follow_upstream_redirects(self, request, target_url: str, upstream_path: str) -> bool:
        """Follow redirects internally so we can rewrite URLs in the final HTML."""
        print(f"[ODOO HANDLER] should_follow_upstream_redirects: target_url={target_url}, path={upstream_path}")
        print(f"[ODOO HANDLER] Following upstream redirect internally")
        return True

    def should_wrap_in_admin_template(self, request, upstream_path, **kwargs):
        """Force wrapping in admin template for Odoo HTML pages."""
        print(f"[ODOO HANDLER] should_wrap_in_admin_template: upstream_path={upstream_path}, status={kwargs.get('status_code')}, ct={kwargs.get('content_type')}")
        
        # Always wrap Odoo HTML in admin template
        status = kwargs.get('status_code', 200)
        ct = (kwargs.get('content_type') or '').lower()
        
        if status != 200:
            print(f"[ODOO HANDLER] Not wrapping: status {status}")
            return False
        
        if 'text/html' not in ct and 'application/xhtml' not in ct:
            print(f"[ODOO HANDLER] Not wrapping: content_type {ct}")
            return False
        
        # For Odoo, wrap everything that's HTML
        print(f"[ODOO HANDLER] Wrapping in admin template")
        return True

    def passthrough_embed_template_context(self, request, upstream_path, **kwargs):
        """Provide Odoo-specific template context including the body scope flag."""
        print(f"[ODOO HANDLER] Setting embed_enable_odoo_body_scope=True for template")
        return {
            'embed_enable_odoo_body_scope': True
        }

    def try_root_display_shell_response(self, request, endpoint, url_trigger_segment, fetch_upstream_shell=False):
        """Show a splash page for bare root click, redirect to /web through proxy."""
        trigger = url_trigger_segment.strip("/")
        print(f"[ODOO ROOT] {VERSION} - Path: {request.path_info} | Trigger: {trigger}")

        proxy_redirect = f"/pt/admin/{trigger}/web"
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Connecting to Odoo...</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 120px; background: #1f2a44; color: white; }}
        h2 {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h2>Connecting to Odoo...</h2>
    <p>Redirecting to dashboard...</p>
    <script>
        window.location.href = "{proxy_redirect}";
    </script>
</body>
</html>"""

        response = HttpResponse(html, content_type="text/html")
        try:
            from dose.passthrough.forwarding import _wrap_in_admin_template
            wrapped = _wrap_in_admin_template(request, response, trigger, endpoint)
            print(f"[ODOO ROOT] {VERSION} - Wrapped in admin template")
            return wrapped
        except Exception as e:
            print(f"[ODOO ROOT] Wrap failed: {e}")
            return response

    def get_client_side_shim(self, proxy_prefix):
        """Return a client-side JavaScript shim that rewrites fetch/XHR URLs to go through proxy."""
        return f"""
        <script>
        (function() {{
            var PROXY_PREFIX = "{proxy_prefix}";
            var ODOO_PATHS = ['/web', '/odoo', '/report', '/download', '/api', '/base', '/bus'];
            
            function shouldRewriteUrl(url) {{
                if (!url) return false;
                if (url.startsWith(PROXY_PREFIX)) return false; // Already proxied
                if (url.startsWith('http://') || url.startsWith('https://')) return false; // External
                for (var i = 0; i < ODOO_PATHS.length; i++) {{
                    if (url.startsWith(ODOO_PATHS[i])) return true;
                }}
                return false;
            }}
            
            function rewriteUrl(url) {{
                if (shouldRewriteUrl(url)) {{
                    return PROXY_PREFIX + url;
                }}
                return url;
            }}
            
            // Patch fetch
            var _originalFetch = window.fetch;
            window.fetch = function(url, init) {{
                var rewritten = rewriteUrl(url);
                if (rewritten !== url) {{
                    console.debug('[ODOO SHIM] fetch rewrite: ' + url + ' -> ' + rewritten);
                }}
                return _originalFetch.call(this, rewritten, init);
            }};
            
            // Patch XMLHttpRequest
            var _originalOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(method, url, async, user, pass) {{
                var rewritten = rewriteUrl(url);
                if (rewritten !== url) {{
                    console.debug('[ODOO SHIM] XHR rewrite: ' + url + ' -> ' + rewritten);
                }}
                return _originalOpen.call(this, method, rewritten, async, user, pass);
            }};
            
            console.log('[ODOO SHIM] Installed fetch/XHR rewriter. Proxy prefix: ' + PROXY_PREFIX);
        }})();
        </script>
        """

    def process_html_response(self, html_str, request, endpoint_url=None, **context):
        """Inject client-side shim and rewrite asset URLs to route through proxy prefix."""
        if not html_str or not self.endpoint:
            return html_str

        prefix = self.proxy_prefix
        print(f"[ODOO HANDLER] Rewriting HTML with prefix={prefix}")

        # Inject shim right after <head> tag opens
        shim_js = self.get_client_side_shim(prefix)
        html_str = re.sub(
            r'(<head[^>]*>)',
            rf'\1\n{shim_js}',
            html_str,
            count=1,
            flags=re.IGNORECASE
        )

        # Rewrite /web/*, /odoo/*, /report/*, etc. paths to go through proxy prefix
        # Captures: src/href = " or ' + absolute path starting with /
        html_str = re.sub(
            r'(src|href)=(["\'])(/(web|odoo|report|download|base|api)[^"\']*)',
            rf'\1=\2{prefix}\3\2',
            html_str,
            flags=re.IGNORECASE
        )

        print(f"[ODOO HANDLER] Rewriting complete (shim injected, asset URLs rewritten)")
        return html_str
