"""Relay upstream root-absolute navigations back onto their proxy prefix.

An upstream SPA sometimes navigates the browser to a root-absolute path of its
own (e.g. a silent-auth refresh falling back from an iframe to a redirect).
Served from our origin that request arrives at OUR root, outside any proxy
prefix, so the forwarder never sees it and the pane goes blank.

Page script cannot fix this: window.location and Location's href/assign are
[LegacyUnforgeable] in every current browser (verified in Chrome --
Object.getOwnPropertyDescriptor(window, 'location').configurable is false and
Location.prototype.href does not exist), so a client shim cannot intercept the
navigation. The relay therefore happens server-side, which is also what a plain
browser round-trip would look like.

Endpoint-specific knowledge stays in the handler: a handler opts in by defining

    def stray_root_paths(self):
        return ("/auth",)

This module only aggregates that hook across discovered handlers and derives the
proxy prefix from the same-origin Referer, so no app name or path ever appears
in shared code.
"""
from __future__ import annotations

import logging
from urllib.parse import urlparse

from dose.passthrough.registry import _discover_handler_classes

logger = logging.getLogger(__name__)


def _claimed_by_any_handler(path: str) -> bool:
    for cls in _discover_handler_classes():
        try:
            fn = getattr(cls(), "stray_root_paths", None)
            if not callable(fn):
                continue
            for claimed in fn() or ():
                if path == claimed or path.startswith(claimed.rstrip("/") + "/"):
                    return True
        except Exception:
            logger.exception("stray_root_paths failed for %s", cls.__name__)
    return False


def _proxy_prefix_from_referer(request) -> str:
    """Proxy prefix of the page that triggered the navigation, or ''.

    Only same-origin referers are trusted, and only their leading
    "/<mount>/<sub>/<host>" segments are used, so the prefix can never be
    steered to an arbitrary path by a foreign page.
    """
    referer = request.META.get("HTTP_REFERER") or ""
    if not referer:
        return ""
    parsed = urlparse(referer)
    if parsed.netloc and parsed.netloc != request.get_host():
        return ""
    segments = [s for s in (parsed.path or "").split("/") if s]
    if len(segments) < 3:
        return ""
    return "/" + "/".join(segments[:3])


def resolve_stray_root_relay(request) -> str | None:
    """Target URL to relay this request to, or None to leave it alone."""
    path = getattr(request, "path_info", "") or ""
    if not path or path.startswith("/pt/") or not _claimed_by_any_handler(path):
        return None

    prefix = _proxy_prefix_from_referer(request)
    if not prefix or path.startswith(prefix):
        return None

    target = prefix.rstrip("/") + path
    query = request.META.get("QUERY_STRING") or ""
    if query:
        target += "?" + query
    logger.info("[stray-root-relay] %s -> %s", path, target)
    return target
