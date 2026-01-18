"""
OSTicket proxy views - wraps OSTicket in Django admin interface
"""
import logging
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required

logger = logging.getLogger(__name__)


@staff_member_required
@require_http_methods(["GET", "POST"])
def osticket_wrapper(request):
    """
    Wraps OSTicket interface in Django admin template.
    The actual passthrough is handled by middleware at /admin/osticket/
    This view displays an iframe that loads the passthrough content.
    """
    logger.info(f"[OSTICKET] Wrapper view called for {request.path_info}")

    context = {
        'title': 'OSTicket',
        'osticket_url': '/admin/osticket-content/',  # This will be intercepted by middleware
    }

    return render(request, 'admin/osticket_wrapper.html', context)


@staff_member_required
@require_http_methods(["GET", "POST"])
def osticket_content(request):
    """
    This endpoint serves the actual OSTicket content.
    It's intercepted by the middleware which forwards the request to the external OSTicket server.
    """
    logger.info(f"[OSTICKET] Content endpoint called for {request.path_info}")

    # The middleware will intercept this and forward it to OSTicket
    # If we reach here, return a placeholder
    from django.http import HttpResponse
    return HttpResponse("<p>Loading OSTicket...</p>")
