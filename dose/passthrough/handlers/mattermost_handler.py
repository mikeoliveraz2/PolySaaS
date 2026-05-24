# dose/passthrough/handlers/mattermost_handler.py

import logging
from django.http import HttpResponse

logger = logging.getLogger(__name__)

class MattermostHandler:
    """
    Self-contained Mattermost Passthrough Handler.
    Everything Mattermost-related lives here. No external dependencies.
    """

    def __init__(self):
        self.service_name = "Mattermost"

    def _get_proxy_prefix(self, request):
        """Get the proxy prefix from the request path."""
        path = getattr(request, 'path', '')
        if '/pt/admin/polysaas-mattermost.onrender.com' in path:
            return '/pt/admin/polysaas-mattermost.onrender.com'
        return ''

    def _rewrite_static_urls(self, html_str: str, proxy_prefix: str) -> str:
        """Rewrite static assets to go through our proxy."""
        if not html_str or not proxy_prefix:
            return html_str

        replacements = [
            ('/static/', f'{proxy_prefix}/static/'),
            ('/plugins/', f'{proxy_prefix}/plugins/'),
            ('/api/', f'{proxy_prefix}/api/'),
            ('href="/', f'href="{proxy_prefix}/'),
            ('src="/', f'src="{proxy_prefix}/'),
            ("href='/", f"href='{proxy_prefix}/"),
            ("src='/", f"src='{proxy_prefix}/"),
        ]

        for old, new in replacements:
            html_str = html_str.replace(old, new)

        return html_str

    def _inject_shim(self, html_str: str, proxy_prefix: str, base_origin: str) -> str:
        """Inject basic PolySaaS shim for Mattermost."""
        shim = f"""
        <script>
            console.log('[PolySaaS Mattermost] Shim injected');
            window.POLYSAAS_PROXY_PREFIX = "{proxy_prefix}";
            window.POLYSAAS_BASE_ORIGIN = "{base_origin}";
        </script>
        """
        if '</head>' in html_str:
            return html_str.replace('</head>', shim + '</head>')
        return html_str + shim

    def process_html_response(self, html_str, request, endpoint_url=None):
        """Main method called by the forwarder."""
        logger.info("[MattermostHandler] Processing HTML response")

        path = getattr(request, 'path', '')
        html_lower = (html_str or '').lower()

        is_login_page = (
            '/login' in path.lower() or
            'log in' in html_lower or
            'forgot your password' in html_lower
        )

        proxy_prefix = self._get_proxy_prefix(request)

        # Always rewrite asset URLs
        if proxy_prefix:
            html_str = self._rewrite_static_urls(html_str, proxy_prefix)

        # Special case for login page - preserve original
        if is_login_page:
            logger.info("[MattermostHandler] Preserving native login page")
            return html_str, None

        # For other pages, inject shim
        if proxy_prefix and html_str:
            base_origin = (endpoint_url or "https://polysaas-mattermost.onrender.com").rstrip('/')
            html_str = self._inject_shim(html_str, proxy_prefix, base_origin)

        logger.info("[MattermostHandler] HTML processing done")
        return html_str, None

    def handle_request(self, request, endpoint_url):
        """Fallback hook if needed."""
        logger.debug(f"[MattermostHandler] Handling request: {request.path}")
        return None  # Let the generic forwarder continue
    
# Bottom of D:\PolySaaS\dose\passthrough\handlers\mattermost_handler.py
from dose.passthrough.handlers.registry import register_handler

register_handler("mattermost", MattermostHandler)
print("✅ MattermostHandler registered successfully")