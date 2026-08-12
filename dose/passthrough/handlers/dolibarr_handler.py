# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Mattermost slug identity + SSO Town Square working — 2026-08-02 — see documentation/BINGO_MATTERMOST_SLUG_IDENTITY_SSO_WORKING_2026-08-02.md
# dose/passthrough/handlers/dolibarr_handler.py
"""
Dolibarr passthrough handler.

Dolibarr is a server-rendered PHP app — no Vue/React SPA, no display shell needed.
The only job here is rewriting root-relative asset/navigation URLs in HTML responses
so that /theme/, /core/, /includes/, etc. are served through the PolySaaS proxy prefix
instead of escaping to the upstream origin.

No try_root_display_shell_response — pages render directly inside the Jazzmin content
area via the generic forwarder.
"""
import re
import logging
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Module-level cache for DOLSESSID cookies keyed by endpoint ID.
# Avoids modifying the Django session (which would issue a new sessionid
# cookie and break the PolySaaS login loop).
_DOLSESSID_CACHE: dict[str, dict] = {}  # {ep_id: {"name": ..., "value": ..., "ts": ...}}
_CACHE_TTL = 3600  # 1 hour

# Root-relative paths that Dolibarr embeds in HTML and that must be prefixed.
# Order matters: longer prefixes first to avoid partial matches.
_DOLI_PROXY_PREFIXES = (
    "/includes/",
    "/theme/",
    "/core/",
    "/public/",
    "/custom/",
    "/install/",
    "/document/",
    "/viewimage.php",
    "/user/",
    "/support/",
    "/admin/",
    "/societe/",
    "/compta/",
    "/commande/",
    "/contact/",
    "/projet/",
    "/product/",
    "/facture/",
    "/fourn/",
    "/hrm/",
    "/expensereport/",
    "/holiday/",
    "/ticket/",
    "/ecm/",
    "/agenda/",
    "/reception/",
    "/expedition/",
    "/printing/",
    "/cashdesk/",
    "/loan/",
    "/emailcollector/",
    "/partnership/",
    "/membertools/",
    "/eventorganization/",
    "/recruitment/",
)

# Query-string-only paths that should NOT be prefixed (they're absolute action URLs)
_DOLI_SKIP_PATTERNS = (
    "//",
    "javascript:",
    "mailto:",
    "tel:",
    "#",
    "data:",
)


def _nc_upstream_base_aliases(base: str) -> list:
    b = (base or "").rstrip("/")
    if not b:
        return []
    out = {b}
    if "localhost" in b:
        out.add(b.replace("localhost", "127.0.0.1", 1))
    if "127.0.0.1" in b:
        out.add(b.replace("127.0.0.1", "localhost", 1))
    return list(out)


class DolibarrPassthroughHandler:
    """
    Lightweight handler for Dolibarr passthrough.
    Rewrites root-relative and upstream-absolute URLs in HTML so assets
    and page navigation stay inside the PolySaaS proxy prefix.
    """

    @classmethod
    def matches_endpoint(cls, endpoint) -> bool:
        slug = (getattr(endpoint, "slug", "") or "").lower().strip()
        if slug == "dolibarr":
            return True
        url = (getattr(endpoint, "endpoint_url", "") or "").lower()
        return "dolibarr" in url

    def process_html_response(self, html_str: str, request, endpoint_url: str = None, *args, **kwargs) -> str:
        """Called by forward_request_standardized after fetching upstream HTML."""
        if not html_str:
            return html_str

        endpoint = getattr(request, "_passthrough_endpoint", None)
        poly_prefix = (getattr(request, "_polysniffer_proxy_prefix", None) or "").strip()
        proxy_prefix = poly_prefix.rstrip("/") if poly_prefix else self._proxy_prefix(endpoint, endpoint_url)
        base = self._base_from_url(endpoint_url)

        html_str = self._rewrite_paths(html_str, proxy_prefix, base)
        return html_str

    def _endpoint_id(self, request) -> str:
        endpoint = getattr(request, "_passthrough_endpoint", None) or getattr(request, "_polysniffer_endpoint", None)
        return str(getattr(endpoint, "pk", None) or getattr(endpoint, "id", None) or 0)

    def postprocess_upstream_response(self, resp, request, **context):
        """Cache the upstream Dolibarr session cookie so GET token and POST session match."""
        try:
            for name, value in resp.cookies.get_dict().items():
                if name.startswith("DOLSESSID_"):
                    ep_id = self._endpoint_id(request)
                    _DOLSESSID_CACHE[ep_id] = {"name": name, "value": value, "ts": time.time()}
                    print(f"[DOLI-HANDLER] cached {name}={value[:8]}... for ep={ep_id}")
                    break
        except Exception:
            pass
        return resp

    def override_upstream_cookies(self, request, target_url: str) -> dict:
        """Force the cached Dolibarr session cookie on every upstream request."""
        ep_id = self._endpoint_id(request)
        entry = _DOLSESSID_CACHE.get(ep_id)
        if entry and entry.get("name") and (time.time() - entry.get("ts", 0) < _CACHE_TTL):
            return {entry["name"]: entry["value"]}
        return {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _proxy_prefix(endpoint, endpoint_url: str) -> str:
        if endpoint is not None:
            if hasattr(endpoint, "get_proxy_prefix"):
                return endpoint.get_proxy_prefix().rstrip("/")
        host = urlparse(endpoint_url or "").netloc
        return f"/pt/admin/{host}" if host else "/pt/admin"

    @staticmethod
    def _base_from_url(endpoint_url: str) -> str:
        if not endpoint_url:
            return ""
        p = urlparse(endpoint_url)
        return f"{p.scheme}://{p.netloc}"

    def _should_proxy(self, url: str, proxy_prefix: str) -> bool:
        if not url:
            return False
        for skip in _DOLI_SKIP_PATTERNS:
            if url.startswith(skip):
                return False
        if url.startswith(proxy_prefix):
            return False
        if url.startswith("/"):
            for pfx in _DOLI_PROXY_PREFIXES:
                if url.startswith(pfx):
                    return True
            # Also catch bare PHP files at root (e.g. /index.php?mainmenu=...)
            if re.match(r"^/[a-z0-9_-]+\.php", url, re.IGNORECASE):
                return True
        return False

    def _to_proxy(self, url: str, proxy_prefix: str, base_aliases: list) -> str:
        if not url or not isinstance(url, str):
            return url
        # Absolute upstream URLs
        for ab in base_aliases:
            if url.startswith(ab + "/"):
                return proxy_prefix + url[len(ab):]
            if url == ab:
                return proxy_prefix + "/"
        # Root-relative
        if self._should_proxy(url, proxy_prefix):
            return proxy_prefix + url
        return url

    def _rewrite_attr(self, match, proxy_prefix: str, base_aliases: list) -> str:
        attr = match.group(1)
        quote = match.group(2)
        val = match.group(3)
        new_val = self._to_proxy(val.strip(), proxy_prefix, base_aliases)
        if new_val == val:
            return match.group(0)
        return f"{attr}={quote}{new_val}{quote}"

    def _rewrite_paths(self, html: str, proxy_prefix: str, base: str) -> str:
        """Rewrite URLs in HTML attributes, url() CSS calls, and JS location assigns."""
        base_aliases = _nc_upstream_base_aliases(base)

        # Stash <script> bodies — never bulk-rewrite JS source (breaks JSON / logic)
        scripts: list[tuple[str, str, str]] = []

        def _stash_script(m: re.Match) -> str:
            scripts.append((m.group(1), m.group(2), m.group(3)))
            return f"__DOLI_SCRIPT_{len(scripts) - 1}__"

        html = re.sub(r"(?is)(<script\b[^>]*>)(.*?)(</script\s*>)", _stash_script, html)

        # Stash <style> bodies (will get url() rewriting only)
        styles: list[tuple[str, str, str]] = []

        def _stash_style(m: re.Match) -> str:
            styles.append((m.group(1), m.group(2), m.group(3)))
            return f"__DOLI_STYLE_{len(styles) - 1}__"

        html = re.sub(r"(?is)(<style\b[^>]*>)(.*?)(</style\s*>)", _stash_style, html)

        # Rewrite href / src / action / data-url in markup
        attr_pat = (
            r"(?i)\b(href|src|action|data-url|data-href|data-link|data-src|poster)"
            r"\s*=\s*([\"'])([^\"']*)\2"
        )

        def _rewrite_match(m: re.Match) -> str:
            return self._rewrite_attr(m, proxy_prefix, base_aliases)

        html = re.sub(attr_pat, _rewrite_match, html)

        # url() in markup/style strings (root-relative only — safe)
        def _rewrite_url_call(m: re.Match) -> str:
            q, path = m.group(1), m.group(2).strip()
            new_path = self._to_proxy(path, proxy_prefix, base_aliases)
            if new_path == path:
                return m.group(0)
            return f"url({q}{new_path}{q})"

        html = re.sub(
            r'url\(\s*(["\'])(/[^"\')\s]*)\1\s*\)',
            _rewrite_url_call,
            html,
            flags=re.IGNORECASE,
        )

        # Restore <style> blocks with url() rewriting inside them
        for i, (open_tag, inner, close_tag) in enumerate(styles):
            rewritten_inner = re.sub(
                r'url\(\s*(["\'])(/[^"\')\s]*)\1\s*\)',
                _rewrite_url_call,
                inner,
                flags=re.IGNORECASE,
            )
            html = html.replace(f"__DOLI_STYLE_{i}__", open_tag + rewritten_inner + close_tag)

        # Restore <script> blocks untouched (body) but rewrite src= on opening tag
        def _rewrite_script_open(m: re.Match) -> str:
            return self._rewrite_attr(m, proxy_prefix, base_aliases)

        for i, (open_tag, inner, close_tag) in enumerate(scripts):
            rw_open = re.sub(attr_pat, _rewrite_script_open, open_tag)
            html = html.replace(f"__DOLI_SCRIPT_{i}__", rw_open + inner + close_tag)

        print(f"[DOLI-HANDLER] HTML rewrite complete: proxy={proxy_prefix!r} base={base!r}")
        return html

    def handle_static_asset(self, request_path, ext_path_str):
        """Not needed for Dolibarr — assets proxy through generic forwarder."""
        return None
