# dose/passthrough/handlers/nextcloud_handler.py
import re
import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class NextcloudPassthroughHandler:
    """
    Handler for Nextcloud passthrough.
    Rewrites asset URLs to load directly from Nextcloud origin,
    and navigation URLs to stay within the /pt/ passthrough prefix.
    """

    STATIC_EXTENSIONS = (
        '.css', '.js', '.woff', '.woff2', '.ttf', '.eot', '.otf',
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
        '.map', '.json'
    )

    STATIC_PREFIXES = (
        '/core/', '/apps/', '/dist/', '/cspviolations',
        '/ocs/', '/avatar/', '/index.php/avatar',
    )

    def process_html_response(self, html_str, response, endpoint_url=None, *args, **kwargs):
        logger.info("[NEXTCLOUD HANDLER] Processing response")

        if not endpoint_url:
            return html_str, None

        origin = endpoint_url.rstrip('/')
        parsed = urlparse(origin)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"

        content = html_str

        content = self._rewrite_static_assets(content, base_origin)
        content = self._rewrite_navigation(content, base_origin)
        content = self._inject_base_fix(content, base_origin)

        return content, None

    def _rewrite_static_assets(self, html, base_origin):
        """Rewrite src= and href= for static assets to load from Nextcloud directly."""
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

    def _rewrite_navigation(self, html, base_origin):
        """Keep navigation links within passthrough, rewrite API calls to origin."""
        def rewrite_ocs(match):
            url = match.group(1)
            return f'"{base_origin}{url}"'

        html = re.sub(r'"(/ocs/v[12]\.php/[^"]*)"', rewrite_ocs, html)
        html = re.sub(r'"(/remote\.php/[^"]*)"', rewrite_ocs, html)
        html = re.sub(r'"(/index\.php/apps/[^"]*)"', rewrite_ocs, html)

        return html

    def _inject_base_fix(self, html, base_origin):
        """Inject a script that patches Nextcloud's generateUrl to use the origin."""
        patch_script = f"""
<script>
(function() {{
    if (window.OC && window.OC.generateUrl) {{
        var origGenUrl = window.OC.generateUrl;
        window.OC.generateUrl = function(url, params, options) {{
            var result = origGenUrl.call(this, url, params, options);
            if (result.startsWith('/') && !result.startsWith('/pt/')) {{
                var isStatic = /\\.(css|js|woff2?|ttf|png|jpg|svg|ico|gif|webp)/.test(result);
                var isApi = result.startsWith('/ocs/') || result.startsWith('/remote.php/');
                if (isStatic || isApi) {{
                    return '{base_origin}' + result;
                }}
            }}
            return result;
        }};
    }}
    if (window.OC && window.OC.filePath) {{
        var origFilePath = window.OC.filePath;
        window.OC.filePath = function(app, type, file) {{
            var result = origFilePath.call(this, app, type, file);
            if (result.startsWith('/')) {{
                return '{base_origin}' + result;
            }}
            return result;
        }};
    }}
}})();
</script>
"""
        if '</body>' in html:
            html = html.replace('</body>', patch_script + '</body>')
        else:
            html += patch_script

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
        """Standard stub for static asset handling."""
        return None
