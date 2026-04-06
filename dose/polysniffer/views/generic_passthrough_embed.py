# dose/polysniffer/views/generic_passthrough_embed.py
# Single embed entry point for all PolySniffer server-side passthrough handlers.

import traceback

from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse
from django.utils.html import escape

from ..handlers.registry import get_handler


@staff_member_required
def generic_passthrough_embed(request, service_name, endpoint_id):
    """
    One view for all services: registry picks the handler; handler does fetch + rewrite.
    URL: /pt/admin/passthrough/<service_name>/<endpoint_id>/
    """
    handler_class = get_handler(service_name)
    if not handler_class:
        return HttpResponse(
            f"<h1>Unsupported service</h1><p>{escape(service_name)}</p>",
            status=400,
            content_type="text/html; charset=utf-8",
        )

    try:
        handler = handler_class(endpoint_id, request)
        return handler.embed(request)
    except Http404:
        return HttpResponse(
            "<h1>PassThroughEndpoint not found</h1>"
            f"<p>No PassThroughEndpoint with id=<strong>{escape(str(endpoint_id))}</strong> "
            "in the <strong>current tenant</strong>, or tenant context is missing.</p>"
            f"<p>Service: <code>{escape(service_name)}</code></p>"
            "<p>Open <strong>Admin → Pass through endpoints</strong> for this tenant and use "
            "the ID shown there.</p>",
            status=404,
            content_type="text/html; charset=utf-8",
        )
    except Exception as exc:
        tb = traceback.format_exc()
        body = (
            "<h1>Passthrough embed error</h1>"
            f"<p>service=<strong>{escape(service_name)}</strong> "
            f"endpoint_id=<strong>{escape(str(endpoint_id))}</strong></p>"
            f"<pre>{escape(str(exc))}</pre>"
            f"<pre>{escape(tb)}</pre>"
        )
        return HttpResponse(body, status=500, content_type="text/html; charset=utf-8")
