# File: polysniffer/handlers/mattermost_handler.py
# Purpose: Clean Mattermost handler using the new BasePassthroughHandler

import json
import logging
import re

from .base import BasePassthroughHandler

logger = logging.getLogger(__name__)

class MattermostPassthroughHandler(BasePassthroughHandler):
    """
    Mattermost handler using server-side fetch + processing.
    Much simpler and more reliable than the old proxy+shim approach.
    """

    def get_upstream_cookies(self, request):
        """Return cookies needed for Mattermost SSO."""
        try:
            from dose.models import TenantApp
            from dose.utils import get_current_tenant

            tenant = get_current_tenant(request)
            ta = TenantApp.objects.filter(
                tenant=tenant, 
                app_name='mattermost', 
                status='active'
            ).first()

            if ta and ta.extra_config:
                token = (ta.extra_config.get('mmauthtoken') or 
                         ta.extra_config.get('mm_session_token'))
                if token:
                    return {'MMAUTHTOKEN': token}
        except Exception as e:
            logger.warning(f"[MattermostHandler] Cookie lookup failed: {e}")

        return {}

    def process_html_response(
        self,
        html_str,
        request,
        endpoint_url=None,
        inject_toolbar=True,
        rewrite_assets=True,
    ):
        """Process the fully built Mattermost HTML."""
        logger.info("[MattermostPassthroughHandler] Processing final HTML")

        if not endpoint_url:
            return html_str, None

        proxy_prefix = "/pt/admin/mattermost"

        # Basic cleaning
        html_str = self._strip_base_tags(html_str)
        html_str = self._strip_meta_redirects(html_str)
        html_str = self._strip_csp(html_str)

        # First script in <head>: localStorage + cookie + MM client hints (before webpack path)
        html_str = self._inject_early_mm_token(html_str, request)

        html_str = self._inject_webpack_public_path(html_str, proxy_prefix)

        if rewrite_assets:
            html_str = self._rewrite_static_assets(html_str, proxy_prefix)

        if inject_toolbar:
            html_str = self._inject_toolbar(html_str)

        return html_str, None

    def _inject_early_mm_token(self, html_str, request):
        """Inject MMAUTHTOKEN into page context before Mattermost bundles run."""
        token = ""
        try:
            cookies = self.get_upstream_cookies(request) or {}
            token = (cookies.get("MMAUTHTOKEN") or "").strip()
        except Exception as exc:
            logger.warning(
                "[MattermostPassthroughHandler] Token lookup failed: %s", exc
            )

        if not token:
            return html_str

        token_js = json.dumps(token)
        early = (
            "<script>(function(){var token="
            + token_js
            + ";if(!token)return;"
            "try{"
            "localStorage.setItem('MMAUTHTOKEN',token);"
            "document.cookie='MMAUTHTOKEN='+encodeURIComponent(token)"
            + "+'; path=/; max-age=7200; SameSite=Lax';"
            "window.MMAUTHTOKEN=token;"
            "console.log('[PolySniffer] Strong early token injected');"
            "if(window.location.pathname.indexOf('/login')>=0||"
            "window.location.search.indexOf('redirect_to')>=0){"
            "setTimeout(function(){window.location.reload();},600);}"
            "}catch(e){console.warn('[PolySniffer] Token injection failed:',e);}"
            "})();</script>"
        )
        if re.search(r"<head[^>]*>", html_str, flags=re.IGNORECASE):
            return re.sub(
                r"(?i)(<head[^>]*>)", r"\1" + early, html_str, count=1
            )
        return early + html_str

    def _inject_webpack_public_path(self, html, proxy_prefix):
        """Run before main.js: webpack chunk loaders honor __webpack_public_path__."""
        base = f"{proxy_prefix}/static/"
        snippet = (
            f'<script>try{{window.__webpack_public_path__="{base}";}}catch(e){{}}</script>'
        )
        if re.search(r"<head[^>]*>", html, flags=re.IGNORECASE):
            return re.sub(
                r"(?i)(<head[^>]*>)", r"\1" + snippet, html, count=1
            )
        return snippet + html

    def _rewrite_static_assets(self, html, proxy_prefix):
        """Nuclear rewrite for building pen / embed output (webpack chunks + static + origin)."""
        # Catch every possible webpack chunk and asset
        html = re.sub(
            r'(src|href)=(["\'])([^"\']*?[\w\.-]{5,}\.(js|css|png|jpg|jpeg|gif|svg|woff2?|ttf|eot|json|map|ico))',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html,
            flags=re.IGNORECASE,
        )

        # Force all /static/ paths
        html = re.sub(
            r'(src|href)=(["\'])(/static/[^"\']*)',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html,
            flags=re.IGNORECASE,
        )

        # Bare hashed files at root
        html = re.sub(
            r'(src|href)=(["\'])(/)([\w\.-]{8,}\.(js|css))',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}/static{m.group(3)}{m.group(4)}{m.group(2)}',
            html,
            flags=re.IGNORECASE,
        )

        # Absolute Mattermost origin
        if hasattr(self, "endpoint") and self.endpoint.endpoint_url:
            origin = self.endpoint.endpoint_url.rstrip("/")
            html = re.sub(
                re.escape(origin) + r'(/[^"\']*)',
                lambda m: proxy_prefix + m.group(1),
                html,
                flags=re.IGNORECASE,
            )

        return html

    def _inject_toolbar(self, html):
        """Inject the green toolbar at the top."""
        toolbar = '''
        <div id="polysniffer-toolbar" style="position:fixed;top:0;left:0;right:0;height:52px;background:#000;color:#0f0;z-index:2147483647;font-weight:bold;display:flex;align-items:center;justify-content:center;border-bottom:4px solid #0f0;">
            🟢 PolySniffer ACTIVE — Capturing Mattermost
        </div>
        '''
        # Insert right after <body> tag
        html = re.sub(r'(<body[^>]*>)', r'\1' + toolbar, html, flags=re.IGNORECASE, count=1)
        return html

    def _strip_base_tags(self, html):
        import re
        return re.sub(r"<base\b[^>]*>", "", html, flags=re.IGNORECASE)

    def _strip_meta_redirects(self, html):
        import re
        return re.sub(r'<meta\s+http-equiv\s*=\s*["\']refresh["\'][^>]*>', "", html, flags=re.IGNORECASE)

    def _strip_csp(self, html):
        import re
        return re.sub(r'<meta\s+http-equiv\s*=\s*["\']Content-Security-Policy["\'][^>]*>', "", html, flags=re.IGNORECASE)
