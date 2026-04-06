# Auto-generated PassthroughHandler for Mattermost
# Generated from PolySniffer analysis of http://localhost:8065
# 
# This handler provides:
# - SSO via get_upstream_cookies()
# - URL rewriting for static assets and API calls
# - Client-side shim for dynamic requests (fetch, XHR, WebSocket)
# - Strict enforcement of /pt/admin/mattermost/ prefix

import json
import logging
import re
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class MattermostPassthroughHandler:
    """
    Passthrough handler for Mattermost.
    Generated from PolySniffer captures - do not hand-edit.
    Regenerate from fresh captures if behavior changes.
    """

    def process_html_response(self, html_str, request, endpoint_url=None, *args, **kwargs):
        """
        Process upstream HTML for embedded display in PolySaaS admin.
        """
        logger.info("[MattermostPassthroughHandler] Processing HTML response")

        if not endpoint_url:
            return html_str, None

        origin = endpoint_url.rstrip("/")
        parsed = urlparse(origin)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"
        proxy_prefix = "/pt/admin/mattermost"

        # Strip tags that break embedding
        html_str = self._strip_base_tags(html_str)
        html_str = self._strip_meta_redirects(html_str)
        html_str = self._strip_csp(html_str)

        # BROADER SERVER-SIDE REWRITING - Catch ALL static/chunk files
        # Critical for webpack-based SPAs like Mattermost with hashed chunks
        # (e.g. 3949.58b56486b08018682f8b.css, main.eba7751588c9635a9465.js)
        html_str = re.sub(
            r'(src|href)=(["\'])(/[^"\']+\.(js|css|png|jpg|jpeg|gif|svg|woff2?|ttf|eot|json|map))\2',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html_str,
            flags=re.IGNORECASE
        )

        # Extra pass for any remaining /static/ paths (catches files without extensions)
        html_str = re.sub(
            r'(src|href)=(["\'])(/static/[^"\']+)\2',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html_str
        )

        # Inject client-side shim for dynamic requests
        html_str = self._inject_client_shim(html_str, base_origin, request, proxy_prefix)

        return html_str, None

    def get_upstream_cookies(self, request):
        """
        Provide session cookies for SSO/auto-login to Mattermost.
        Mattermost primarily uses MMAUTHTOKEN header/cookie.
        """
        try:
            from dose.models import TenantApp
            from dose.utils import get_current_tenant
            import requests as _req

            tenant = get_current_tenant(request)
            if not tenant:
                return {}

            ta = TenantApp.objects.filter(
                tenant=tenant, app_name='mattermost', status='active'
            ).first()

            if not ta or not ta.extra_config:
                return {}

            # Try cached MMAUTHTOKEN first (check multiple possible key names)
            token = (ta.extra_config.get('mmauthtoken') or 
                     ta.extra_config.get('mm_session_token') or
                     ta.extra_config.get('mm_token'))
            token_time = (ta.extra_config.get('mmauthtoken_time') or 
                          ta.extra_config.get('mm_session_token_time', 0))

            if token and (time.time() - token_time < 3600):
                logger.info("[MattermostPassthroughHandler] Using cached token: %s...", token[:8] if token else 'None')
                return {'MMAUTHTOKEN': token}

            # Refresh session if needed (check multiple possible key names)
            password = (ta.extra_config.get('mattermost_password') or 
                        ta.extra_config.get('mm_password') or
                        ta.extra_config.get('password'))
            if not password:
                logger.warning("[MattermostPassthroughHandler] No password available in extra_config")
                return {}

            login_id = (ta.extra_config.get('mattermost_login_id') or 
                        ta.extra_config.get('mm_login_id') or
                        request.user.email)

            resp = _req.post(
                'http://localhost:8065/api/v4/users/login',
                json={'login_id': login_id, 'password': password},
                timeout=10,
            )

            if resp.status_code == 200:
                token = resp.headers.get('Token')
                if token:
                    # Save with both key names for compatibility
                    ta.extra_config['mmauthtoken'] = token
                    ta.extra_config['mmauthtoken_time'] = time.time()
                    ta.extra_config['mm_session_token'] = token
                    ta.extra_config['mm_session_token_time'] = time.time()
                    ta.save(update_fields=['extra_config'])
                    logger.info("[MattermostPassthroughHandler] MMAUTHTOKEN refreshed: %s...", token[:8])
                    return {'MMAUTHTOKEN': token}

        except Exception as exc:
            logger.warning("[MattermostPassthroughHandler] get_upstream_cookies failed: %s", exc)

        return {}

    def _strip_base_tags(self, html):
        return re.sub(r"<base\b[^>]*>", "", html, flags=re.IGNORECASE)

    def _strip_meta_redirects(self, html):
        return re.sub(r'<meta\s+http-equiv\s*=\s*["\']refresh["\'][^>]*>', "", html, flags=re.IGNORECASE)

    def _strip_csp(self, html):
        return re.sub(r'<meta\s+http-equiv\s*=\s*["\']Content-Security-Policy["\'][^>]*>', "", html, flags=re.IGNORECASE)

    def _inject_client_shim(self, html, base_origin, request, proxy_prefix):
        """
        Minimal diagnostic shim: token + basic pushState guard only.
        Injected as the first thing inside <head> so passthrough_embed extraction keeps it.
        """
        token = ""
        try:
            cookies = self.get_upstream_cookies(request) or {}
            token = cookies.get("MMAUTHTOKEN") or ""
            if token:
                logger.info(
                    "[MattermostPassthroughHandler] MINIMAL token ready: %s...",
                    token[:8],
                )
            else:
                logger.warning(
                    "[MattermostPassthroughHandler] MINIMAL: no MMAUTHTOKEN from get_upstream_cookies"
                )
        except Exception as exc:
            logger.warning("[MattermostPassthroughHandler] Token retrieval failed: %s", exc)

        token_js = json.dumps(token)
        proxy_js = json.dumps(proxy_prefix)

        shim = f"""
<script data-polysaas-mattermost-shim="1">
(function() {{
    var MMAUTHTOKEN = {token_js};
    var PROXY = {proxy_js};

    if (MMAUTHTOKEN) {{
        try {{
            localStorage.setItem('MMAUTHTOKEN', MMAUTHTOKEN);
            document.cookie = 'MMAUTHTOKEN=' + MMAUTHTOKEN + '; path=/; SameSite=Lax; max-age=3600';
            window.MMAUTHTOKEN = MMAUTHTOKEN;
            console.log('[PolySaaS MINIMAL] MMAUTHTOKEN injected: ' + MMAUTHTOKEN.substring(0, 8) + '...');
        }} catch (e) {{
            console.warn('[PolySaaS MINIMAL] Token injection failed:', e);
        }}
    }} else {{
        console.warn('[PolySaaS MINIMAL] No MMAUTHTOKEN available');
    }}

    var originalPushState = history.pushState;
    history.pushState = function(state, title, url) {{
        if (url && (url === '/' || String(url).indexOf('/dose/') !== -1)) {{
            console.log('[PolySaaS MINIMAL] Blocked pushState to:', url);
            return;
        }}
        return originalPushState.apply(this, arguments);
    }};

    console.log('[PolySaaS MINIMAL] Shim loaded - proxy:', PROXY);
}})();
</script>
"""

        if re.search(r"<head\b", html, re.IGNORECASE):
            return re.sub(
                r"(<head[^>]*>)",
                lambda m: m.group(1) + shim,
                html,
                count=1,
                flags=re.IGNORECASE,
            )
        return shim + html
