"""API endpoint for client-side navigation orchestration triggers."""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


@login_required
def orchestration_navigate_api(request):
    """Receive client-side navigation events and trigger orchestration hook."""
    if request.method != 'POST':
        return JsonResponse({'status': 'ok'})

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'invalid json'}, status=400)

    upstream_path = body.get('path', '/')
    method = body.get('method', 'GET').upper()

    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return JsonResponse({'status': 'no_tenant'})

    # Fire the orchestration hook
    from dose.passthrough.orchestration_hook import check_orchestration_trigger

    # Create a mock-like request with the correct method for matching
    request.method = method
    check_orchestration_trigger(request, upstream_path, app_name='odoo', tenant=tenant)

    return JsonResponse({'status': 'ok', 'path': upstream_path})
