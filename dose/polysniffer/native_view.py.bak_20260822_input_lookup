"""Serve the captured browser into the PolySniffer workspace pane.

The pane shows the real browser rather than the upstream application's HTML, so
applications that refuse to be framed, or that will only run against a session
they established themselves, still appear in the workspace. Frames go out as a
multipart stream an <img> can consume, and gestures come back as small JSON
posts, which keeps this on the existing WSGI server with no WebSocket.
"""
from __future__ import annotations

import json
import time

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods

from dose.polysniffer.native_browser_capture import (
    native_browser_is_running,
    next_native_frame,
    queue_native_input,
)
from dose.polysniffer.sniff_tenant import bind_request_tenant
from dose.utils import get_current_tenant

_BOUNDARY = "polysnifferframe"
_STREAM_SECONDS = 600
_IDLE_TIMEOUT = 1.0


def _tenant_schema(request) -> str:
    tenant = bind_request_tenant(request) or get_current_tenant(request)
    return getattr(tenant, "schema_name", "") or ""


def _frame_stream(tenant_schema: str, endpoint_host: str):
    deadline = time.monotonic() + _STREAM_SECONDS
    seq = 0
    while time.monotonic() < deadline:
        if not native_browser_is_running(
            tenant_schema=tenant_schema, endpoint_host=endpoint_host
        ):
            return
        seq, frame = next_native_frame(
            tenant_schema=tenant_schema,
            endpoint_host=endpoint_host,
            after_seq=seq,
            timeout=_IDLE_TIMEOUT,
        )
        if not frame:
            continue
        yield (
            f"--{_BOUNDARY}\r\n"
            f"Content-Type: image/jpeg\r\n"
            f"Content-Length: {len(frame)}\r\n\r\n"
        ).encode("ascii")
        yield frame
        yield b"\r\n"


@staff_member_required
@require_http_methods(["GET"])
def native_stream(request, endpoint_host: str):
    schema = _tenant_schema(request)
    if not schema:
        return JsonResponse({"error": "no tenant context"}, status=400)
    response = StreamingHttpResponse(
        _frame_stream(schema, endpoint_host),
        content_type=f"multipart/x-mixed-replace; boundary={_BOUNDARY}",
    )
    response["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response["X-Accel-Buffering"] = "no"
    return response


@staff_member_required
@require_http_methods(["POST"])
def native_input(request, endpoint_host: str):
    schema = _tenant_schema(request)
    if not schema:
        return JsonResponse({"error": "no tenant context"}, status=400)
    try:
        event = json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "invalid event"}, status=400)
    if not isinstance(event, dict) or not event.get("kind"):
        return JsonResponse({"error": "invalid event"}, status=400)
    delivered = queue_native_input(
        tenant_schema=schema, endpoint_host=endpoint_host, event=event
    )
    if not delivered:
        return JsonResponse({"error": "no native browser running"}, status=409)
    return JsonResponse({"ok": True})
