# dose/views/hs_asset_proxy.py
"""
HubSpot asset proxy — fetches a static.hsappstatic.net JS file, patches
window.location.hostname/origin checks so HubSpot's FireAlarm LoginUI
validator sees 'app.hubspot.com' when running inside PolySaaS passthrough.

Only FireAlarmUI bundles are proxied (all other CDN assets load directly).
Responses are cached keyed by URL — CDN files are immutable/versioned so a
long TTL is safe.
"""
from __future__ import annotations

import hashlib
import logging

import requests
from django.core.cache import cache
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)

_ALLOWED_HOSTS = (
    "static.hsappstatic.net",
    "static2.hsappstatic.net",
)

_CACHE_TTL = 3600  # 1 hour — CDN assets are immutable; safe to cache

_HOSTNAME_PATCH = (
    "window.location.hostname",
    '(window.__PS_HUBSPOT_LOCATION_SPOOF?"app.hubspot.com":window.location.hostname)',
)
_ORIGIN_PATCH = (
    "window.location.origin",
    '(window.__PS_HUBSPOT_LOCATION_SPOOF?"https://app.hubspot.com":window.location.origin)',
)


def _cache_key(url: str) -> str:
    return "hs_asset_proxy:" + hashlib.md5(url.encode()).hexdigest()


def _fetch_and_patch(src_url: str) -> tuple[str, str]:
    """Return (patched_js, content_type)."""
    resp = requests.get(src_url, timeout=15, headers={
        "User-Agent": "Mozilla/5.0 (compatible; PolySaaS-AssetProxy/1.0)",
    })
    resp.raise_for_status()
    ct = resp.headers.get("Content-Type", "application/javascript")
    js = resp.text
    old, new = _HOSTNAME_PATCH
    js = js.replace(old, new)
    old2, new2 = _ORIGIN_PATCH
    js = js.replace(old2, new2)
    return js, ct


@require_GET
@cache_control(max_age=3600, public=True)
def hs_asset_proxy(request):
    src = request.GET.get("src", "").strip()
    if not src:
        return HttpResponse("Missing src", status=400, content_type="text/plain")

    from urllib.parse import urlparse
    parsed = urlparse(src)
    if parsed.scheme not in ("http", "https") or not any(
        parsed.netloc == h or parsed.netloc.endswith("." + h) for h in _ALLOWED_HOSTS
    ):
        return HttpResponse("Forbidden src", status=403, content_type="text/plain")

    key = _cache_key(src)
    cached = cache.get(key)
    if cached:
        js, ct = cached
    else:
        try:
            js, ct = _fetch_and_patch(src)
            cache.set(key, (js, ct), _CACHE_TTL)
        except Exception as exc:
            logger.warning("[hs_asset_proxy] fetch failed for %s: %s", src, exc)
            return HttpResponse(f"Upstream fetch failed: {exc}", status=502, content_type="text/plain")

    # Ensure content-type is JS even if CDN sends something odd
    if "javascript" not in ct.lower():
        ct = "application/javascript; charset=utf-8"
    return HttpResponse(js, content_type=ct)
