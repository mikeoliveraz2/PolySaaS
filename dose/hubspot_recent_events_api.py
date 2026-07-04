"""
API endpoint for polling recent HubSpot-driven orchestration events.

Used by the HubSpot passthrough "iframe + green bar" view: the bar itself
cannot inspect the cross-origin HubSpot iframe (browser same-origin policy
makes that impossible), so instead it polls this same-origin endpoint for the
latest CallBackData rows produced by the HubSpot webhook -> orchestration ->
atomic-service pipeline (e.g. HubSpotToOdooContactSync), and surfaces them via
the existing (frozen) orchestration_instruction_button.js showEvent() API.
"""
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

logger = logging.getLogger(__name__)


@login_required
def hubspot_recent_events_api(request):
    """Return the most recent CallBackData rows from HubSpot webhook orchestration."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        from dose.utils import get_current_tenant
        tenant = get_current_tenant(request)
    if not tenant:
        return JsonResponse({'status': 'no_tenant', 'events': []})

    from dose.models import CallBackData

    since_id = request.GET.get('since_id')
    qs = CallBackData.objects.filter(matchingEventKey__startswith='hubspot:').order_by('-pub_date')
    if since_id:
        try:
            qs = qs.filter(id__gt=int(since_id))
        except (TypeError, ValueError):
            pass

    rows = list(qs[:5])
    events = [
        {
            'id': row.id,
            'description': row.description,
            'matchingEventKey': row.matchingEventKey,
            'pub_date': row.pub_date.isoformat() if row.pub_date else None,
        }
        for row in rows
    ]
    return JsonResponse({'status': 'ok', 'events': events})
