"""
Passthrough Views - Direct access to external services
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.template.response import TemplateResponse
from urllib.parse import urlparse
import logging

from dose.models import PassThroughEndpoint

logger = logging.getLogger(__name__)


@staff_member_required
def direct_service_view(request, endpoint_id):
    """
    Redirect to proper middleware passthrough route - NO IFRAMES

    This view redirects to the proper trigger_path URL which the middleware
    will handle. The middleware does all the passthrough work:
    - Proxies requests to external service
    - Rewrites URLs in HTML responses
    - Handles form submissions
    - Maintains session state

    NO IFRAMES - uses proper middleware-based passthrough architecture.
    """
    from django.shortcuts import redirect

    endpoint = get_object_or_404(PassThroughEndpoint, id=endpoint_id)

    if not endpoint.endpoint_url:
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest("Endpoint URL is required")

    if not endpoint.trigger_path:
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest("Trigger path is required. Please configure the trigger path in the PassThrough Endpoint admin.")

    # Build the proper passthrough URL based on trigger_path
    # The middleware will handle requests to this path
    trigger = endpoint.trigger_path.strip('/')

    # If trigger_path contains slashes, use it as-is
    # Otherwise, default to /dose/{trigger}/ for regular users or /admin/{trigger}/ for admin
    if '/' in trigger:
        passthrough_url = f'/{trigger}/'
    else:
        # Simple name - default to /dose/{trigger}/ (middleware handles both /dose/ and /admin/)
        passthrough_url = f'/dose/{trigger}/'

    # Debug logging
    logger.info(f"[DIRECT_SERVICE] Endpoint ID: {endpoint_id}, redirecting to: {passthrough_url}")
    print(f"[DIRECT_SERVICE] Endpoint ID: {endpoint_id}", flush=True)
    print(f"[DIRECT_SERVICE] Trigger path: {endpoint.trigger_path}", flush=True)
    print(f"[DIRECT_SERVICE] Redirecting to: {passthrough_url}", flush=True)
    print(f"[DIRECT_SERVICE] Middleware will handle passthrough to: {endpoint.endpoint_url}", flush=True)

    # Redirect to the middleware passthrough route
    return redirect(passthrough_url)


@login_required
def passthrough_service(request, service, page=None):
    """
    Main passthrough view for external services
    Routes to appropriate service handler based on service parameter
    URL pattern: /admin/passthrough/<service>/
    URL pattern: /admin/passthrough/<service>/<path:page>
    """
    logger.info(f"Passthrough request: service={service}, page={page}, user={request.user.username}")

    # Service routing
    service_handlers = {
        'gmail': handle_gmail_passthrough,
    }

    handler = service_handlers.get(service.lower())
    if not handler:
        logger.warning(f"Unknown service requested: {service}")
        return HttpResponseNotFound(f"Service '{service}' not found")

    return handler(request)


def handle_gmail_passthrough(request):
    """
    Gmail service passthrough handler
    Renders Gmail interface within admin template using structured data
    """
    logger.info(f"Gmail passthrough for user: {request.user.username}")
    # Placeholder - implement if needed
    from django.contrib.admin import site
    context = site.each_context(request)
    context.update({
        'service_name': 'Gmail',
        'service_type': 'gmail',
        'page_title': 'Gmail Integration',
        'service_content': '<p>Gmail passthrough - use direct service view instead</p>',
    })
    return TemplateResponse(request, 'admin/passthrough.html', context)




@csrf_exempt
def passthrough_api(request, service):
    """
    API endpoint for passthrough services
    Handles AJAX requests from passthrough interfaces
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    logger.info(f"Passthrough API: service={service}, method={request.method}")

    # Service-specific API handling can be added here
    return JsonResponse({
        'status': 'success',
        'service': service,
        'message': f'{service.title()} API call processed'
    })
