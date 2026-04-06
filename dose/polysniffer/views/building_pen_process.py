# dose/polysniffer/views/building_pen_process.py
# POST: final built HTML → single handler pass (toolbar + asset rewrite).

import json
import logging
import traceback

from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.utils.html import escape
from django.views.decorators.http import require_POST

from ..handlers.registry import get_handler

logger = logging.getLogger(__name__)


@staff_member_required
@require_POST
def building_pen_process(request):
    """
    Accept JSON { service_name, endpoint_id, html }.
    One process_html_response pass: rewrite assets + toolbar (minimal building pen).
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponseBadRequest("Invalid JSON")

    service_name = data.get("service_name")
    endpoint_id = data.get("endpoint_id")
    html = data.get("html")

    if not service_name or endpoint_id is None or not isinstance(html, str):
        return HttpResponseBadRequest("Missing service_name, endpoint_id, or html")

    handler_class = get_handler(service_name)
    if not handler_class:
        return HttpResponseBadRequest("Unsupported service")

    try:
        eid = int(endpoint_id)
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid endpoint_id")

    try:
        handler = handler_class(eid, request)
    except Http404:
        return HttpResponse(
            "<h1>PassThroughEndpoint not found</h1>",
            status=404,
            content_type="text/html; charset=utf-8",
        )

    endpoint_url = (getattr(handler.endpoint, "endpoint_url", None) or "").strip() or None
    try:
        processed_html, django_response = handler.process_html_response(
            html,
            request,
            endpoint_url=endpoint_url,
            inject_toolbar=True,
            rewrite_assets=True,
        )
    except Exception as exc:
        logger.exception("[building_pen_process] handler failed: %s", exc)
        tb = traceback.format_exc()
        return HttpResponse(
            f"<h1>Processing error</h1><pre>{escape(tb)}</pre>",
            status=500,
            content_type="text/html; charset=utf-8",
        )

    if django_response is not None:
        return django_response

    return HttpResponse(
        processed_html,
        content_type="text/html; charset=utf-8",
        status=200,
    )
