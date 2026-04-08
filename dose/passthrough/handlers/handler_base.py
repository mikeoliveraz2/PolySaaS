"""
Base class for endpoint-specific passthrough handlers (Shela / Michael pattern).

- **trigger_path** on PassThroughEndpoint defines the /pt/admin/<trigger>/ URL segment only.
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
    """Build /pt/admin/<segment>/ from trigger_path (not slug)."""
    raw = (endpoint.trigger_path or "").strip("/").lower().split("/")[-1].replace("-", "_")
    return f"/pt/admin/{raw}"


def endpoint_log_label(endpoint: PassThroughEndpoint) -> str:
    """Prefer slug for logs when set; otherwise trigger_path."""
    s = (getattr(endpoint, "slug", None) or "").strip()
    if s:
        return s
    return (endpoint.trigger_path or "").strip() or "endpoint"


class PassthroughHandlerBase:
    """
    Optional base for handlers that receive the ORM endpoint and shared helpers.
    Subclasses override handle() when wired to dumb middleware; until then the
    existing registry returns stateless handler instances for forward_request_standardized.
    """

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
