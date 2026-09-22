"""API endpoint for client-side navigation orchestration triggers."""
# Owner-approved 2026-09-22: Type 3 — standing_by hint when invoice SPA path has Post refine bound.
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


def _invoice_standing_by(tenant, upstream_path: str) -> list:
    """If this is an invoice SPA page and Type 3 enqueue exists, tell the bar to wait for Post."""
    path = (upstream_path or "").lower()
    if not any(
        x in path
        for x in (
            "invoice",
            "account.move",
            "accounting",
            "customer-invoice",
            "vendor-bill",
        )
    ):
        return []
    try:
        from dose.models import Instruction
        from dose.tenant_app_lookup import tenant_schema_search_path

        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                return []
            rows = list(
                Instruction.objects.filter(
                    executescript="EnqueueOdooInvoiceRefine",
                ).order_by("id")[:3]
            )
            if not rows:
                rows = list(
                    Instruction.objects.filter(
                        eventKey__icontains="invoice",
                        executescript__icontains="Refine",
                    ).order_by("id")[:3]
                )
            return [
                (
                    "Type 3 standing by — open draft → Post to refine Note "
                    f"(bound: {r.executescript})"
                )
                for r in rows
            ]
    except Exception:
        logger.exception("standing_by lookup failed")
        return []


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
    standing_by = []
    if matched == 0:
        standing_by = _invoice_standing_by(tenant, upstream_path)
    orch_log(
        'navigate_api_done',
        path=upstream_path,
        matched_req=(result_req or {}).get('matched', 0),
        matched_res=(result_res or {}).get('matched', 0),
        saved=saved,
        standing_by=len(standing_by),
    )

    return JsonResponse({
        'status': 'ok',
        'path': upstream_path,
        'matched': matched,
        'callback_saved': saved,
        'matched_req': (result_req or {}).get('matched', 0),
        'matched_res': (result_res or {}).get('matched', 0),
        'standing_by': standing_by,
        'capture_mailbox_fix': '6d0f7f4e+enroll_first',
    })
