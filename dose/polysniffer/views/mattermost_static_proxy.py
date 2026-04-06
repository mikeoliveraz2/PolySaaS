# dose/polysniffer/views/mattermost_static_proxy.py
# Stream Mattermost /static/* through Django (same origin as embed).
# Rewrites root-relative /static/ inside JS/CSS bodies so webpack chunk URLs hit this proxy.

import logging

import requests
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.html import escape

logger = logging.getLogger(__name__)

DEFAULT_MM_ORIGIN = "http://localhost:8065"

# Must match MattermostPassthroughHandler proxy_prefix + "/static/"
WEBPACK_STATIC_PREFIX = "/pt/admin/mattermost/static/"

# Main + large chunks; skip huge source maps if needed
MAX_BODY_REWRITE_BYTES = 25 * 1024 * 1024


def _upstream_static_base():
    try:
        from django.conf import settings

        return getattr(settings, "MATTERMOST_STATIC_ORIGIN", DEFAULT_MM_ORIGIN).rstrip("/")
    except Exception:
        return DEFAULT_MM_ORIGIN


def _rewrite_webpack_static_paths(body: bytes, *, is_css: bool) -> bytes:
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

    p = WEBPACK_STATIC_PREFIX
    s = s.replace('"/static/', f'"{p}')
    s = s.replace("'/static/", f"'{p}")
    s = s.replace('\\"/static/', f'\\"{p}')
    s = s.replace("\\'/static/", f"\\'{p}")
    if is_css:
        s = s.replace("url(/static/", f"url({p}")
        s = s.replace('url("/static/', f'url("{p}')
        s = s.replace("url('/static/", f"url('{p}")
    return s.encode("utf-8")


@login_required
def mattermost_static_proxy(request, path):
    """Proxy static files (js, css, images, manifest, etc.) to real Mattermost."""
    if ".." in path or path.startswith("/"):
        return HttpResponse("Invalid path", status=400)

    base = _upstream_static_base()
    real_url = f"{base}/static/{path}"
    if request.META.get("QUERY_STRING"):
        real_url = f"{real_url}?{request.META['QUERY_STRING']}"

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
            content = _rewrite_webpack_static_paths(content, is_css=False)
        elif is_css:
            content = _rewrite_webpack_static_paths(content, is_css=True)
        elif is_json:
            content = _rewrite_webpack_static_paths(content, is_css=False)

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
