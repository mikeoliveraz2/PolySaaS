"""
HubSpot passthrough — discover and remember upstream app origins.

HubSpot does not keep a single stable app base: regional hosts (app-na2.hubspot.com),
generic app.hubspot.com, and post-login paths (/home-beta, /global-home/…) shift after
the first hop. Initial contact must record whatever base HubSpot assigns and reuse it
for HTML + client-side rewrites in the same sniff session.
"""
from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urlparse

_HUBSPOT_APP_HOST_RE = re.compile(
    r"(?:https?:)?//((?:app(?:-[a-z0-9]+)?|local)\.hubspot\.com)",
    re.IGNORECASE,
)
_HUBSPOT_APP_ABS_RE = re.compile(
    r"https?://((?:app(?:-[a-z0-9]+)?|local)\.hubspot\.com)",
    re.IGNORECASE,
)

_CDN_HOST_MARKERS = (
    "static.hsappstatic.net",
    "static2.hsappstatic.net",
    "wt-assets/static-files",
)

_DEFAULT_APP_ORIGINS = (
    "https://app.hubspot.com",
)


def origin_from_url(url: str) -> str:
    return _normalize_origin(url)


def _normalize_origin(origin: str) -> str:
    o = (origin or "").strip().rstrip("/")
    if not o:
        return ""
    parsed = urlparse(o if "://" in o else f"https://{o.lstrip('/')}")
    if not parsed.netloc:
        return ""
    scheme = "https" if parsed.scheme in ("http", "https") else parsed.scheme
    if scheme == "http" and parsed.netloc.endswith(".hubspot.com"):
        scheme = "https"
    return f"{scheme}://{parsed.netloc}".rstrip("/")


def is_hubspot_app_host(host: str) -> bool:
    h = (host or "").lower().split(":", 1)[0]
    if not h.endswith(".hubspot.com"):
        return False
    if any(marker in h for marker in _CDN_HOST_MARKERS):
        return False
    return h == "app.hubspot.com" or h.startswith("app-") or h == "local.hubspot.com"


def is_hubspot_app_origin(origin: str) -> bool:
    try:
        return is_hubspot_app_host(urlparse(origin).netloc)
    except Exception:
        return False


def session_bases_key(endpoint_id: int) -> str:
    return f"hubspot_pt_bases_{endpoint_id}"


def load_known_bases(request, endpoint_id: int | None, endpoint_url: str) -> set[str]:
    bases: set[str] = set()
    configured = origin_from_url(endpoint_url)
    if configured:
        bases.add(configured)
    bases.update(_DEFAULT_APP_ORIGINS)
    if request is not None and endpoint_id is not None:
        try:
            stored = request.session.get(session_bases_key(endpoint_id), [])
            if isinstance(stored, (list, tuple, set)):
                bases.update(str(x) for x in stored if x)
        except Exception:
            pass
    return {b.rstrip("/") for b in bases if b and is_hubspot_app_origin(b.rstrip("/"))}


def remember_bases(request, endpoint_id: int | None, origins: Iterable[str]) -> set[str]:
    if request is None or endpoint_id is None:
        return set()
    key = session_bases_key(endpoint_id)
    current = set(load_known_bases(request, endpoint_id, ""))
    added: set[str] = set()
    for raw in origins:
        origin = origin_from_url(raw) if "://" in (raw or "") else ""
        if not origin and raw:
            origin = origin_from_url(f"https://{(raw or '').lstrip('/')}")
        origin = origin.rstrip("/")
        if origin and is_hubspot_app_origin(origin) and origin not in current:
            current.add(origin)
            added.add(origin)
    if added:
        try:
            request.session[key] = sorted(current)
            request.session.modified = True
        except Exception:
            pass
    return added


def discover_origins_from_text(text: str) -> set[str]:
    if not text:
        return set()
    found: set[str] = set()
    for match in _HUBSPOT_APP_ABS_RE.finditer(text):
        host = match.group(1)
        if is_hubspot_app_host(host):
            found.add(f"https://{host}".rstrip("/"))
    for match in _HUBSPOT_APP_HOST_RE.finditer(text):
        host = match.group(1)
        if is_hubspot_app_host(host):
            found.add(f"https://{host}".rstrip("/"))
    return found


def remember_from_location(request, endpoint_id: int | None, location: str) -> None:
    if not location:
        return
    loc = location.strip()
    if loc.startswith("/"):
        return
    origin = origin_from_url(loc)
    if origin:
        remember_bases(request, endpoint_id, [origin])


def rewrite_location_through_proxy(location: str, proxy_prefix: str, known_bases: set[str]) -> str:
    """Map upstream HubSpot app URLs to the PolySaaS proxy prefix."""
    loc = (location or "").strip()
    prefix = proxy_prefix.rstrip("/")
    if not loc:
        return loc
    if loc.startswith(prefix + "/") or loc == prefix:
        return loc
    if loc.startswith("/"):
        return prefix + loc
    parsed = urlparse(loc)
    if parsed.scheme and parsed.netloc:
        origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        if is_hubspot_app_origin(origin):
            path = parsed.path or "/"
            if not path.startswith("/"):
                path = "/" + path
            qs = f"?{parsed.query}" if parsed.query else ""
            frag = f"#{parsed.fragment}" if parsed.fragment else ""
            return f"{prefix}{path}{qs}{frag}"
        for base in sorted(known_bases, key=len, reverse=True):
            if loc.startswith(base + "/") or loc == base:
                rel = loc[len(base) :]
                if not rel.startswith("/"):
                    rel = "/" + rel
                return prefix + rel
    return loc
