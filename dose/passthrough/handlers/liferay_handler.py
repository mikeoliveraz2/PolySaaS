# dose/passthrough/handlers/liferay_handler.py
import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class LiferayPassthroughHandler:
    """
    Handler for Liferay CE passthrough.
    Rewrites theme/portlet asset URLs to load from the Liferay origin,
    and keeps navigation within the /pt/ passthrough prefix.
    """

    STATIC_EXTENSIONS = (
        '.css', '.js', '.woff', '.woff2', '.ttf', '.eot', '.otf',
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
        '.map', '.json', '.jsp'
    )

    STATIC_PREFIXES = (
        '/o/', '/combo', '/html/', '/image/',
        '/documents/', '/layouttpl/', '/css/',
    )

    def process_html_response(self, html_str, response, endpoint_url=None, *args, **kwargs):
        logger.info("[LIFERAY HANDLER] Processing response")

        if not endpoint_url:
            return html_str, None

        origin = endpoint_url.rstrip('/')
        parsed = urlparse(origin)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"

        content = html_str
        content = self._rewrite_static_assets(content, base_origin)
        content = self._rewrite_theme_urls(content, base_origin)
        content = self._inject_portlet_bridge(content, base_origin)

        return content, None

    def _rewrite_static_assets(self, html, base_origin):
        """Rewrite src= and href= for Liferay static assets."""
        def rewrite_attr(match):
            attr = match.group(1)
            quote = match.group(2)
            url = match.group(3)

            if not url or url.startswith('data:') or url.startswith('javascript:') or url.startswith('#') or url.startswith('mailto:'):
                return match.group(0)
            if url.startswith('http://') or url.startswith('https://') or url.startswith('//'):
                return match.group(0)

            if self._is_static(url):
                return f'{attr}={quote}{base_origin}{url}{quote}'

            return match.group(0)

        pattern = r'(src|href)=([\"\'])(/[^\"\']*?)\2'
        return re.sub(pattern, rewrite_attr, html)

    def _rewrite_theme_urls(self, html, base_origin):
        """Rewrite Liferay theme and combo servlet URLs."""
        html = re.sub(
            r'"/o/([^"]*)"',
            lambda m: f'"{base_origin}/o/{m.group(1)}"',
            html
        )
        html = re.sub(
            r'"/combo\?([^"]*)"',
            lambda m: f'"{base_origin}/combo?{m.group(1)}"',
            html
        )
        html = re.sub(
            r'"/image/([^"]*)"',
            lambda m: f'"{base_origin}/image/{m.group(1)}"',
            html
        )
        return html

    def _inject_portlet_bridge(self, html, base_origin):
        """
        Inject bridge script that patches Liferay's themeDisplay
        to resolve asset URLs against the origin.
        """
        bridge_script = f"""
<script>
(function() {{
    if (window.Liferay) {{
        var origAjax = Liferay.fire;
        window.__POLYSAAS_LIFERAY_ORIGIN__ = '{base_origin}';
    }}
    var origFetch = window.fetch;
    window.fetch = function(url, opts) {{
        if (typeof url === 'string' && url.startsWith('/o/') || url.startsWith('/api/')) {{
            url = '{base_origin}' + url;
        }}
        return origFetch.call(this, url, opts);
    }};
}})();
</script>
"""
        if '</body>' in html:
            html = html.replace('</body>', bridge_script + '</body>')
        else:
            html += bridge_script

        return html

    def _is_static(self, url):
        """Check if a URL points to a static asset."""
        url_lower = url.lower().split('?')[0]
        if any(url_lower.endswith(ext) for ext in self.STATIC_EXTENSIONS):
            return True
        if any(url_lower.startswith(prefix) for prefix in self.STATIC_PREFIXES):
            return True
        return False

    def handle_static_asset(self, request_path, ext_path_str):
        return None
