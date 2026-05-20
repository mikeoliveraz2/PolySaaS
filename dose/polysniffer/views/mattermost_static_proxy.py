# dose/polysniffer/views/mattermost_static_proxy.py
# Stream Mattermost /static/* through Django (same origin as embed).
# Rewrites root-relative /static/ inside JS/CSS bodies so webpack chunk URLs hit this proxy.
# Nested paths under /static/ on the wire (e.g. github/bundle.js) map to upstream
# /static/plugins/<plugin>/...; core trees (images, emoji, …) stay under /static/<path>.

import logging

import requests
from django.http import HttpResponse
from django.utils.html import escape

logger = logging.getLogger(__name__)

# Main + large chunks; skip huge source maps if needed
MAX_BODY_REWRITE_BYTES = 25 * 1024 * 1024

# First path segment after /static/: these are CORE paths that stay on /static/<path> upstream.
# Only "plugins" gets special handling — everything else is a core static asset.
_MM_STATIC_CORE_PREFIXES = frozenset(
    ("images", "emoji", "fonts", "files", "metadata", "sounds", "css", "js", "json", "html", "ico", "txt", "xml", "map")
)


def _upstream_rel_for_mm_static(path: str) -> str:
    """Single upstream path (relative to origin) for one proxy request — no retries."""
    if "/" not in path:
        return f"/static/{path}"
    first, _, _rest = path.partition("/")
    fl = first.lower()
    if fl in _MM_STATIC_CORE_PREFIXES or fl == "plugins":
        return f"/static/{path}"
    # Unknown first segment (e.g. 'com.mattermost.nps', 'github', 'playbooks') = plugin ID.
    # Upstream serves plugin bundles under /static/plugins/<plugin_id>/...
    return f"/static/plugins/{path}"


def _rewrite_webpack_static_paths(body: bytes, *, is_css: bool, webpack_prefix: str) -> bytes:
    """
    Mattermost bundles set publicPath to /static/; chunk loaders request :8000/static/...
    Replace string forms of root-relative /static/ with our proxy path inside file bodies.
    """
    if not body or len(body) > MAX_BODY_REWRITE_BYTES:
        return body
    try:
        s = body.decode("utf-8")
    except UnicodeDecodeError:
        return body

    p = webpack_prefix
    s = s.replace('"/static/', f'"{p}')
    s = s.replace("'/static/", f"'{p}")
    s = s.replace('\\"/static/', f'\\"{p}')
    s = s.replace("\\'/static/", f"\\'{p}")
    if is_css:
        s = s.replace("url(/static/", f"url({p}")
        s = s.replace('url("/static/', f'url("{p}')
        s = s.replace("url('/static/", f"url('{p}")
    return s.encode("utf-8")


def mattermost_static_proxy(request, path, trigger=''):
    """Proxy static files (js, css, images, manifest, etc.) to real Mattermost."""
    if ".." in path or path.startswith("/"):
        return HttpResponse("Invalid path", status=400)

    # Upstream base is the trigger hostname from the URL — no DB lookup.
    base = f"https://{trigger}" if trigger and '.' in trigger else "http://localhost:8065"
    webpack_prefix = f"/pt/admin/{trigger}/static/" if trigger else "/pt/admin/mattermost/static/"
    qs = f"?{request.META['QUERY_STRING']}" if request.META.get("QUERY_STRING") else ""
    real_url = f"{base}{_upstream_rel_for_mm_static(path)}{qs}"

    try:
        upstream = requests.get(
            real_url,
            headers={"User-Agent": request.META.get("HTTP_USER_AGENT", "Mozilla/5.0")},
            timeout=30,
        )

        if upstream.status_code != 200:
            return HttpResponse(status=upstream.status_code)

        content = upstream.content
        ct = (upstream.headers.get("content-type") or "").lower()
        path_l = path.lower()

        is_js = (
            "javascript" in ct
            or "ecmascript" in ct
            or path_l.endswith(".js")
            or path_l.endswith(".mjs")
        )
        is_css = ("css" in ct and "javascript" not in ct) or path_l.endswith(".css")
        is_json = "json" in ct or path_l.endswith(".json")

        if is_js:
            content = _rewrite_webpack_static_paths(content, is_css=False, webpack_prefix=webpack_prefix)
        elif is_css:
            content = _rewrite_webpack_static_paths(content, is_css=True, webpack_prefix=webpack_prefix)
        elif is_json:
            content = _rewrite_webpack_static_paths(content, is_css=False, webpack_prefix=webpack_prefix)

        resp = HttpResponse(
            content,
            content_type=upstream.headers.get(
                "content-type", "application/octet-stream"
            ),
            status=upstream.status_code,
        )
        for h in ("Cache-Control", "ETag", "Last-Modified"):
            if upstream.headers.get(h):
                resp[h] = upstream.headers[h]
        return resp

    except Exception as exc:
        logger.warning("Mattermost static proxy error for %s: %s", path, exc)
        return HttpResponse(
            f"Static proxy error: {escape(str(exc))}",
            status=502,
            content_type="text/plain; charset=utf-8",
        )
