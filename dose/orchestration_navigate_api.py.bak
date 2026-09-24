"""API endpoint for client-side navigation orchestration triggers."""
# Type 3 bar text comes from the Confirm callback (DoseMessage), not this GET.
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


@csrf_exempt
@login_required
def orchestration_navigate_api(request):
    """Receive client-side navigation events and trigger orchestration hook.

    Odoo/Mattermost SPAs report path changes here (no upstream HTTP body).
    Fire both REQ and RES so Instructions on either direction can match.
    CaptureGetResponse enrolls the mailbox even when upstream body is absent.
    """
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
        from dose.utils import get_current_tenant
        tenant = get_current_tenant(request)
    if not tenant:
        from dose.passthrough.orchestration_log import orch_log
        orch_log('navigate_api_no_tenant', path=upstream_path)
        return JsonResponse({'status': 'no_tenant'})

    # Ensure capture/mailbox helpers see the tenant without relying on session alone.
    request.tenant = tenant

    from dose.passthrough.orchestration_hook import check_orchestration_trigger
    from dose.passthrough.orchestration_log import orch_log

    request.method = method
    result_req = check_orchestration_trigger(
        request, upstream_path, app_name='odoo', tenant=tenant, direction='REQ',
    )
    # SPA navigate has no proxied response body; RES still runs so CaptureGetResponse
    # Instructions (direction=RESPONSE) match and can enroll the mailbox.
    result_res = check_orchestration_trigger(
        request,
        upstream_path,
        app_name='odoo',
        tenant=tenant,
        direction='RES',
        upstream_response=None,
    )
    matched = (result_req or {}).get('matched', 0) + (result_res or {}).get('matched', 0)
    saved = (result_req or {}).get('saved', 0) + (result_res or {}).get('saved', 0)
    orch_log(
        'navigate_api_done',
        path=upstream_path,
        matched_req=(result_req or {}).get('matched', 0),
        matched_res=(result_res or {}).get('matched', 0),
        saved=saved,
    )

    return JsonResponse({
        'status': 'ok',
        'path': upstream_path,
        'matched': matched,
        'callback_saved': saved,
        'matched_req': (result_req or {}).get('matched', 0),
        'matched_res': (result_res or {}).get('matched', 0),
        'standing_by': [],
        'capture_mailbox_fix': '6d0f7f4e+enroll_first',
    })
