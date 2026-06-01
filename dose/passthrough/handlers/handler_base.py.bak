# =============================================================================
# FROZEN — Mattermost Passthrough BINGO (2026-05-31) [handler hook contract]
# NO CHANGES WITHOUT OWNER PERMISSION (Michael / Shela)
# Certification: documentation/BINGO_MATTERMOST_LOGIN_BRIDGE_AUTO_SSO_2026-05-31.md
# =============================================================================
"""
Base class for endpoint-specific passthrough handlers (Shela / Michael pattern).

- **endpoint_url** hostname becomes the /pt/admin/<hostname>/ URL segment.
- **slug** is optional and separate; use it for non-passthrough identifiers when set.

Handlers that need shared helpers can subclass PassthroughHandlerBase. The legacy
BasePassthroughHandler in __init__.py remains the HTML-rewrite fallback for get_handler().
"""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from django.http import HttpResponse

if TYPE_CHECKING:
    from dose.models import PassThroughEndpoint

logger = logging.getLogger(__name__)


def proxy_prefix_for_trigger_endpoint(endpoint: PassThroughEndpoint) -> str:
    """Build /pt/admin/<segment>/ from endpoint_url hostname."""
    try:
        from urllib.parse import urlparse
        host = urlparse(endpoint.endpoint_url or "").netloc
        return f"/pt/admin/{host}/" if host else "/pt/admin/"
    except:
        return "/pt/admin/"


def endpoint_log_label(endpoint: PassThroughEndpoint) -> str:
    """Prefer slug for logs when set; otherwise endpoint_url hostname."""
    s = (getattr(endpoint, "slug", None) or "").strip()
    if s:
        return s
    try:
        from urllib.parse import urlparse
        host = urlparse(endpoint.endpoint_url or "").netloc
        return host or "endpoint"
    except:
        return "endpoint"


class PassthroughHandlerBase:
    """
    Optional base for handlers that receive the ORM endpoint and shared helpers.
    Subclasses override handle() when wired to dumb middleware; until then the
    existing registry returns stateless handler instances for forward_request_standardized.

    Hook contract for scalable passthrough endpoints:
    - `try_rewrite_incoming_path(request, endpoint) -> bool`
    - `try_root_display_shell_response(request, endpoint, url_trigger_segment) -> HttpResponse | None`
    - `augment_outbound_headers(request, headers, target_url) -> None`
    - `filter_cookies_for_upstream(request, cookies) -> dict`
    - `get_upstream_cookies(request) -> dict`
    - `upstream_url_for_subpath(endpoint_url, clean_path) -> str | None`
    - `should_follow_upstream_redirects(request, target_url, upstream_path) -> bool`
    - `postprocess_upstream_response(resp, request, **context) -> requests.Response`
    - `rewrite_upstream_body(body, content_type, request, **context) -> bytes | None`
    - `process_html_response(html_str, request, endpoint_url=None, **context) -> str | tuple | HttpResponse`
    - `should_forward_set_cookie_headers(request, upstream_content_type, upstream_path, response_kind) -> bool`
    - `should_delegate_pt_admin_core(request, path_info) -> bool` (defer PT core to URLconf)
    - `matches_endpoint(endpoint) -> bool` (class method — registry discovery)
    - `try_rewrite_incoming_path_referer_fallback(request) -> bool` (class method, optional)
    - `fallback_rewrite_html_for_proxy(html, request) -> str` (optional forwarder safety net)
    - `passthrough_embed_template_context(trigger, request) -> dict` (optional embed template flags)
    - `should_process_html_response(request, upstream_path, **kwargs) -> bool` (optional HTML rewrite gate)
    - `should_wrap_in_admin_template(request, upstream_path, **kwargs) -> bool` (optional admin embed wrap gate)
    - `extra_blocked_upstream_prefixes(request, upstream_path) -> tuple` (optional paths to block at forwarder)
    - `coerce_upstream_response_for_path(resp, request, upstream_path) -> tuple|None` (optional API HTML→JSON stub)
    """

    _GENERIC_NON_HTML_SUFFIXES = (
        ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg",
        ".woff", ".woff2", ".ttf", ".eot", ".json", ".map", ".ico",
    )
    _GENERIC_NON_EMBED_PREFIXES = ("/api/", "/static/")

    def __init__(self, endpoint: PassThroughEndpoint | None = None):
        self.endpoint = endpoint

    @property
    def proxy_prefix(self) -> str:
        if self.endpoint is None:
            return "/pt/admin/unknown"
        return proxy_prefix_for_trigger_endpoint(self.endpoint)

    def handle(self, request):
        """Override in subclass when handler owns full request/response."""
        raise NotImplementedError("Handler must implement handle()")

    def try_rewrite_incoming_path(self, request, endpoint) -> bool:
        return False

    def try_root_display_shell_response(self, request, endpoint, url_trigger_segment):
        return None

    def augment_outbound_headers(self, request, headers: dict, target_url: str) -> None:
        return None

    def filter_cookies_for_upstream(self, request, cookies: dict) -> dict:
        return cookies

    def get_upstream_cookies(self, request) -> dict:
        return {}

    def upstream_url_for_subpath(self, endpoint_url, clean_path):
        return None

    def native_passthrough_prefixes(self):
        return ()

    def should_exempt_csrf_for_path(self, path_info: str) -> bool:
        for prefix in self.native_passthrough_prefixes():
            if path_info == prefix or path_info.startswith(prefix + "/"):
                return True
        return False

    def should_delegate_pt_admin_core(self, request, path_info: str) -> bool:
        return False

    def should_follow_upstream_redirects(self, request, target_url: str, upstream_path: str) -> bool:
        return False

    def postprocess_upstream_response(self, resp, request, **context):
        return resp

    def rewrite_upstream_body(self, body, content_type, request, **context):
        return None

    def needs_readable_response_body(self, request, target_url: str) -> bool:
        """Return True if this handler needs the response body to be readable (uncompressed).
        
        When True, the forwarder will set Accept-Encoding: identity to prevent
        upstream from sending compressed responses. Override in subclasses that
        need to read/rewrite response bodies.
        
        Default is False to preserve browser's Accept-Encoding for HAR parity.
        """
        return False

    def get_request_body(self, request, target_url: str) -> bytes | None:
        """Override to rewrite the outgoing request body before forwarding. Return None to use request.body as-is."""
        return None

    def process_html_response(self, html_str, request, endpoint_url=None, **context):
        return html_str

    def should_forward_set_cookie_headers(
        self,
        request,
        *,
        upstream_content_type=None,
        upstream_path=None,
        response_kind=None,
    ) -> bool:
        return True

    def extra_blocked_upstream_prefixes(self, request, upstream_path: str):
        """Return extra upstream path prefixes the forwarder must not proxy (WS upgrade, etc.)."""
        return ()

    @classmethod
    def _generic_non_embeddable_html_path(cls, upstream_path: str) -> bool:
        """True when upstream path looks like assets/API, not an HTML app shell."""
        path = upstream_path or "/"
        if any(path.endswith(ext) for ext in cls._GENERIC_NON_HTML_SUFFIXES):
            return True
        return any(path.startswith(prefix) for prefix in cls._GENERIC_NON_EMBED_PREFIXES)

    def should_process_html_response(
        self,
        request,
        upstream_path: str,
        *,
        content_type=None,
        status_code=200,
    ) -> bool:
        """Return False to skip process_html_response for API/asset HTML mis-responses."""
        if status_code != 200:
            return False
        ct = (content_type or "").lower()
        if "text/html" not in ct and "application/xhtml" not in ct:
            return False
        return not self._generic_non_embeddable_html_path(upstream_path)

    def should_wrap_in_admin_template(
        self,
        request,
        upstream_path: str,
        *,
        content_type=None,
        status_code=200,
    ) -> bool:
        """Return False to pass HTML through without admin/passthrough_embed wrap."""
        return self.should_process_html_response(
            request,
            upstream_path,
            content_type=content_type,
            status_code=status_code,
        )

    def search_and_replace_assets(self, content: str, asset_types=None) -> str:
        if asset_types is None:
            asset_types = ["img", "js", "css"]
        prefix = self.proxy_prefix
        for t in asset_types:
            content = re.sub(
                rf'src=["\'](/[^"\']+\.{re.escape(t)})["\']',
                rf'src="{prefix}\1"',
                content,
                flags=re.I,
            )
        return content

    def forward_cookies(self, response):
        return response

    def inject_requesttoken(self, response):
        return response

    def log_passthrough_stream(self, response, request):
        label = endpoint_log_label(self.endpoint) if self.endpoint else "unknown"
        print(
            f"[PASSTHROUGH SNIFFER] {label} | Path: {request.path} | "
            f"Status: {getattr(response, 'status_code', 'n/a')}"
        )
        return response
