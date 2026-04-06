# File: polysniffer/handlers/mattermost_handler.py
# Purpose: Clean Mattermost handler using the new BasePassthroughHandler

import re
import logging
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

    def process_html_response(self, html_str, request, endpoint_url=None):
        """Process the fully built Mattermost HTML."""
        logger.info("[MattermostPassthroughHandler] Processing final HTML")

        if not endpoint_url:
            return html_str, None

        proxy_prefix = "/pt/admin/mattermost"

        # Basic cleaning
        html_str = self._strip_base_tags(html_str)
        html_str = self._strip_meta_redirects(html_str)
        html_str = self._strip_csp(html_str)

        # Rewrite static assets
        html_str = self._rewrite_static_assets(html_str, proxy_prefix)

        # Inject green PolySniffer toolbar
        html_str = self._inject_toolbar(html_str)

        return html_str, None

    def _rewrite_static_assets(self, html, proxy_prefix):
        """Rewrite all static asset URLs."""
        import re
        # Broad catch for hashed webpack files
        html = re.sub(
            r'(src|href)=(["\'])([^"\']*?[\w.-]+\.(js|css|png|jpg|jpeg|gif|svg|woff2?|ttf|eot|json|map))',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html,
            flags=re.IGNORECASE
        )
        # Extra pass for /static/
        html = re.sub(
            r'(src|href)=(["\'])(/static/[^"\']*)',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html,
            flags=re.IGNORECASE
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
