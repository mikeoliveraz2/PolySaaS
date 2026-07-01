"""
PolySniffer — optional passthrough handler hooks (generic aggregation only).

Endpoint-specific path lists and browse entry URLs live on handlers, not here.
Derived from direct HAR families via handler implementations (e.g. HubSpot _BYPASS_PREFIXES).
"""
from __future__ import annotations

from dose.passthrough.handlers.handler_base import PassthroughHandlerBase


def non_page_path_prefixes(handler, request, upstream_path: str = "/") -> tuple[str, ...]:
    """API/asset path prefixes — not HTML page navigations (workspace shell routing)."""
    seen: set[str] = set()
    ordered: list[str] = []

    def _add(prefixes):
        for raw in prefixes or ():
            p = (raw or "").strip()
            if not p:
                continue
            key = p.lower()
            if key not in seen:
                seen.add(key)
                ordered.append(p if p.startswith("/") else f"/{p}")

    _add(PassthroughHandlerBase._GENERIC_NON_EMBED_PREFIXES)
    if handler is not None and hasattr(handler, "polysniffer_non_page_path_prefixes"):
        try:
            _add(handler.polysniffer_non_page_path_prefixes(request))
        except Exception:
            pass
    if handler is not None and hasattr(handler, "extra_blocked_upstream_prefixes"):
        try:
            _add(handler.extra_blocked_upstream_prefixes(request, upstream_path))
        except Exception:
            pass
    return tuple(ordered)


def workspace_browse_subpath(handler, endpoint, request=None) -> str:
    """First HTML page for PolySniffer workspace embed."""
    if handler is not None and hasattr(handler, "resolve_workspace_browse_subpath"):
        try:
            sub = handler.resolve_workspace_browse_subpath(request, endpoint)
            if sub:
                return sub if sub.startswith("/") else f"/{sub}"
        except Exception:
            pass
    if handler is not None and hasattr(handler, "polysniffer_workspace_browse_subpath"):
        try:
            sub = handler.polysniffer_workspace_browse_subpath(endpoint, request=request)
            if sub:
                return sub if sub.startswith("/") else f"/{sub}"
        except Exception:
            pass
    uri = (getattr(endpoint, "starting_uri", None) or "").strip()
    if uri:
        return uri if uri.startswith("/") else f"/{uri}"
    return "/login/"


def path_looks_like_non_page(subpath: str, handler=None, request=None) -> bool:
    """True when path is API/asset traffic (HAR: /api/, CDN, etc.) — not a shell page nav."""
    path = f"/{(subpath or '').lstrip('/')}"
    if PassthroughHandlerBase._generic_non_embeddable_html_path(path):
        return True
    low = path.lower()
    for prefix in non_page_path_prefixes(handler, request, path):
        p = prefix if prefix.startswith("/") else f"/{prefix}"
        if low.startswith(p.lower()):
            return True
    last = path.rstrip("/").split("/")[-1]
    if "." in last and not last.startswith("."):
        ext = last.rsplit(".", 1)[-1].lower()
        if ext in PassthroughHandlerBase._GENERIC_NON_HTML_SUFFIXES:
            return True
    return False
