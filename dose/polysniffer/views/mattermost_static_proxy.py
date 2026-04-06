# dose/polysniffer/views/mattermost_static_proxy.py
# Stream Mattermost /static/* through Django (same origin as embed).

import logging

import requests
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.html import escape

logger = logging.getLogger(__name__)

# Default upstream; override via MATTERMOST_STATIC_ORIGIN in settings if needed.
DEFAULT_MM_ORIGIN = "http://localhost:8065"


def _upstream_static_base():
    try:
        from django.conf import settings

        return getattr(settings, "MATTERMOST_STATIC_ORIGIN", DEFAULT_MM_ORIGIN).rstrip("/")
    except Exception:
        return DEFAULT_MM_ORIGIN


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
            stream=True,
        )

        if upstream.status_code == 200:
            streaming = StreamingHttpResponse(
                upstream.iter_content(chunk_size=8192),
                content_type=upstream.headers.get(
                    "content-type", "application/octet-stream"
                ),
                status=upstream.status_code,
            )
            for h in ("Cache-Control", "ETag", "Last-Modified"):
                if upstream.headers.get(h):
                    streaming[h] = upstream.headers[h]
            return streaming

        return HttpResponse(status=upstream.status_code)

    except Exception as exc:
        logger.warning("Mattermost static proxy error for %s: %s", path, exc)
        return HttpResponse(
            f"Static proxy error: {escape(str(exc))}",
            status=502,
            content_type="text/plain; charset=utf-8",
        )
