"""
HubSpot — PolySniffer native sniff HTML rewrites.

HubSpot login loads assets from //static.hsappstatic.net/… (protocol-relative CDN).
Generic native fallback prefixes //… with the sniff proxy →
/dose/sniff/<id>/native//static.hsappstatic.net/… → 404 on app-na2.hubspot.com.

This processor keeps CDN URLs direct (https) and routes app paths through sniff prefix.
Also patches native upstream resolution so mistaken CDN-via-proxy paths still load.
"""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from dose.polysniffer.handlers.hubspot_bases import (
    discover_origins_from_text,
    is_hubspot_app_host,
    load_known_bases,
    remember_bases,
)

if TYPE_CHECKING:
    from dose.passthrough.handlers.hubspot_handler import HubspotPassthroughHandler

logger = logging.getLogger(__name__)

_CDN_HOSTS = (
    "static.hsappstatic.net",
    "static2.hsappstatic.net",
)

_CDN_PATH_MARKERS = _CDN_HOSTS + ("wt-assets/static-files",)


def _base_origin(endpoint_url: str) -> str:
    parsed = urlparse((endpoint_url or "").strip())
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""


def _is_html(content_type: str) -> bool:
    ct = (content_type or "").lower()
    return "text/html" in ct or "application/xhtml" in ct


def _is_cdn_url(path: str) -> bool:
    low = (path or "").lower()
    return any(marker in low for marker in _CDN_PATH_MARKERS)


def _cdn_https_url(path: str) -> str | None:
    """Turn mistaken proxy/CDN path shapes into direct https CDN URL."""
    raw = (path or "").strip()
    if not raw:
        return None
    if raw.startswith("//"):
        host = raw[2:].split("/", 1)[0].lower()
        if any(host == h or host.endswith("." + h) for h in _CDN_HOSTS):
            return "https:" + raw
        return None
    if raw.startswith("/"):
        segment = raw.lstrip("/")
        host = segment.split("/", 1)[0].lower()
        if any(host == h for h in _CDN_HOSTS):
            return f"https://{segment}"
    return None


def _rewrite_protocol_relative_app_hosts(html: str, proxy_prefix: str) -> str:
    """//app-na2.hubspot.com/… → proxy prefix (before generic // → https)."""
    prefix = proxy_prefix.rstrip("/")

    def _repl(match: re.Match) -> str:
        attr, quote, host, rest = match.group(1), match.group(2), match.group(3), match.group(4)
        if not is_hubspot_app_host(host):
            return match.group(0)
        path = rest or "/"
        if not path.startswith("/"):
            path = "/" + path
        return f"{attr}={quote}{prefix}{path}{quote}"

    html = re.sub(
        r"(src|href)=(['\"])//((?:app(?:-[a-z0-9]+)?|local)\.hubspot\.com)(/[^'\"]*)?",
        _repl,
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r'(["\'])//((?:app(?:-[a-z0-9]+)?|local)\.hubspot\.com)(/[^"\']*)?\1',
        lambda m: (
            f'{m.group(1)}{prefix}{(m.group(3) or "/")}{m.group(1)}'
            if is_hubspot_app_host(m.group(2))
            else m.group(0)
        ),
        html,
        flags=re.IGNORECASE,
    )
    return html


def _rewrite_absolute_app_bases(html: str, known_bases: set[str], proxy_prefix: str) -> str:
    prefix = proxy_prefix.rstrip("/")
    for origin in sorted(known_bases, key=len, reverse=True):
        base = origin.rstrip("/")
        if not base:
            continue
        html = html.replace(f'"{base}/', f'"{prefix}/')
        html = html.replace(f"'{base}/", f"'{prefix}/")
        html = html.replace(f'"{base}"', f'"{prefix}"')
        html = html.replace(f"'{base}'", f"'{prefix}'")
    return html


def _rewrite_protocol_relative_cdn(html: str) -> str:
    """//static.hsappstatic.net/… → https://static.hsappstatic.net/…"""
    html = re.sub(
        r"(src|href)=(['\"])(//(?:static(?:2)?\.hsappstatic\.net|wt-assets)[^'\"]*)",
        r"\1=\2https:\3\2",
        html,
        flags=re.IGNORECASE,
    )
    # Inline JSON / script string literals HubSpot embeds for bundle loaders.
    html = re.sub(
        r'(["\'])(//static(?:2)?\.hsappstatic\.net/[^"\']+)\1',
        lambda m: f'{m.group(1)}https:{m.group(2)}{m.group(1)}',
        html,
        flags=re.IGNORECASE,
    )
    return html


def _rewrite_root_relative_cdn(html: str) -> str:
    """/static.hsappstatic.net/… → https://static.hsappstatic.net/…"""
    for host in _CDN_HOSTS:
        html = re.sub(
            rf'((?:src|href)=)(["\'])/{re.escape(host)}([^"\']*)',
            rf"\1\2https://{host}\3\2",
            html,
            flags=re.IGNORECASE,
        )
    return html


def _repair_broken_proxy_cdn(html: str, proxy_prefix: str) -> str:
    """Repair /dose/sniff/<id>/native//static.hsappstatic.net/… from older rewriters."""
    prefix = re.escape(proxy_prefix.rstrip("/"))
    html = re.sub(
        prefix + r"//static\.hsappstatic\.net",
        "https://static.hsappstatic.net",
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        prefix + r"/static\.hsappstatic\.net",
        "https://static.hsappstatic.net",
        html,
        flags=re.IGNORECASE,
    )
    return html


def _rewrite_firealarm_scripts(html: str) -> str:
    """
    Rewrite FireAlarmUI script src tags to route through hs-asset-proxy.
    The proxy patches window.location.hostname checks so HubSpot's LoginUI
    validator sees app.hubspot.com instead of localhost.
    Only FireAlarmUI bundles are proxied — all other CDN assets load directly.
    """
    from urllib.parse import quote as _quote

    def _repl(m: re.Match) -> str:
        src = m.group(1)
        proxied = "/dose/hs-asset-proxy/?src=" + _quote(src, safe="")
        return f'src="{proxied}"'

    return re.sub(
        r'src="(https://static(?:2)?\.hsappstatic\.net/FireAlarmUI/[^"]+\.js[^"]*)"',
        _repl,
        html,
        flags=re.IGNORECASE,
    )


def _rewrite_hubspot_native_html(
    html: str,
    *,
    base_origin: str,
    proxy_prefix: str,
    handler: "HubspotPassthroughHandler",
    known_bases: set[str] | None = None,
    request=None,
    endpoint_id: int | None = None,
) -> str:
    bases = set(known_bases or [])
    if base_origin:
        bases.add(base_origin.rstrip("/"))
    discovered = discover_origins_from_text(html)
    bases.update(discovered)
    if request is not None and endpoint_id is not None:
        remember_bases(request, endpoint_id, bases)

    html = re.sub(r"<base\b[^>]*>", "", html, flags=re.IGNORECASE)
    html = re.sub(
        r'<meta\s+http-equiv\s*=\s*["\']Content-Security-Policy["\'][^>]*>',
        "",
        html,
        flags=re.IGNORECASE,
    )

    html = _rewrite_protocol_relative_app_hosts(html, proxy_prefix)
    html = _rewrite_protocol_relative_cdn(html)
    html = _rewrite_root_relative_cdn(html)
    html = _rewrite_absolute_app_bases(html, bases, proxy_prefix)

    def _rewrite_root_path(match: re.Match) -> str:
        attr, quote, path = match.group(1), match.group(2), match.group(3)
        if path.startswith("//") or "://" in path[:20]:
            return match.group(0)
        if _is_cdn_url(path):
            cdn = _cdn_https_url(path)
            return f"{attr}={quote}{cdn}{quote}" if cdn else match.group(0)
        if path.startswith(proxy_prefix):
            return match.group(0)
        if handler._should_proxy_path(path, proxy_prefix):
            return f"{attr}={quote}{proxy_prefix}{path}{quote}"
        low = path.lower()
        # Use /login/ not /login — /loginui/ must not be proxied (CDN bundles).
        if low.startswith(("/login/", "/oauth/", "/api/", "/hs/", "/signup/", "/account/")):
            return f"{attr}={quote}{proxy_prefix}{path}{quote}"
        if low in ("/login", "/oauth"):
            return f"{attr}={quote}{proxy_prefix}{path}{quote}"
        return match.group(0)

    html = re.sub(
        r"(src|href)=(['\"])(/[^'\"]+)",
        _rewrite_root_path,
        html,
        flags=re.IGNORECASE,
    )

    html = re.sub(
        r"(action=)(['\"])(/[^'\"]*)",
        lambda m: (
        f"{m.group(1)}{m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}"
        if not m.group(3).startswith("//")
        and not _is_cdn_url(m.group(3))
        and not m.group(3).lower().startswith("/login")
        else m.group(0)
        ),
        html,
        flags=re.IGNORECASE,
    )

    html = _repair_broken_proxy_cdn(html, proxy_prefix)
    html = _rewrite_firealarm_scripts(html)
    return html


def _endpoint_id_from_proxy_prefix(proxy_prefix: str) -> int | None:
    match = re.search(r"/sniff/(\d+)/(?:native|workspace)", proxy_prefix or "")
    return int(match.group(1)) if match else None


def process_hubspot_native_sniff(
    handler: "HubspotPassthroughHandler",
    body: bytes,
    content_type: str,
    request,
    *,
    endpoint_url: str,
    upstream_path: str,
    proxy_prefix: str,
) -> bytes | None:
    base_origin = _base_origin(endpoint_url)
    if not base_origin or not body or not _is_html(content_type):
        return None

    try:
        html = body.decode("utf-8")
    except UnicodeDecodeError:
        return body

    html = _rewrite_hubspot_native_html(
        html,
        base_origin=base_origin,
        proxy_prefix=proxy_prefix,
        handler=handler,
        known_bases=load_known_bases(
            request,
            getattr(request, "_polysniffer_endpoint_id", None),
            endpoint_url,
        ),
        request=request,
        endpoint_id=getattr(request, "_polysniffer_endpoint_id", None),
    )
    endpoint_id = getattr(request, "_polysniffer_endpoint_id", None) or _endpoint_id_from_proxy_prefix(
        proxy_prefix
    )
    if endpoint_id:
        from dose.polysniffer.workspace_client_capture import inject_workspace_client_capture

        html = inject_workspace_client_capture(html, int(endpoint_id))
    return html.encode("utf-8")


def _patch_native_upstream_resolver() -> None:
    """CDN bundle requests must not be forwarded to app-na2.hubspot.com."""
    try:
        import dose.polysniffer.sniff_forward as sniff_forward
    except Exception:
        logger.debug("hubspot_native_sniff: sniff_forward unavailable for CDN patch")
        return

    if getattr(sniff_forward, "_hubspot_cdn_upstream_patched", False):
        return

    original = sniff_forward._resolve_upstream_url

    def _resolve_upstream_url(endpoint_url: str, subpath: str):
        if "hubspot" in (endpoint_url or "").lower():
            cdn_url = _cdn_https_url(subpath or "")
            if cdn_url:
                return cdn_url, subpath or "/"
        return original(endpoint_url, subpath)

    sniff_forward._resolve_upstream_url = _resolve_upstream_url
    sniff_forward._hubspot_cdn_upstream_patched = True
    logger.info("hubspot_native_sniff: patched native upstream resolver for CDN paths")


def _register() -> None:
    from dose.passthrough.handlers.hubspot_handler import HubspotPassthroughHandler
    from dose.polysniffer.sniff_handler_bridge import register_native_sniff_processor

    register_native_sniff_processor(
        HubspotPassthroughHandler,
        process_hubspot_native_sniff,
    )
    _patch_native_upstream_resolver()


_register()
