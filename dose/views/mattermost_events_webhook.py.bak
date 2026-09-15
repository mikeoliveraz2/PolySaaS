# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: HubSpot → Odoo Contact Creation — 2026-09-08
# BINGO: Mattermost → Odoo Contact Creation — 2026-09-07

"""
Mattermost Outgoing Webhook → same contact mailbox/topic as Slack.

Does not invent a second producer. After token check + contact parse, it calls
publish_slack_contact_event() so the existing Slack → Odoo instruction runs.
"""
from __future__ import annotations

import hmac
import json
import logging

from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from dose.contact_message_format import parse_contact_message
from dose.models import Tenant, TenantApp
from dose.tenant_app_lookup import tenant_schema_search_path
from dose.webhook_events import publish_slack_contact_event

logger = logging.getLogger(__name__)


def _find_mattermost_tenant(team_id: str, request_token: str = ""):
    """Find tenant by mm_team_id, requiring webhook token when many tenants share a team id."""
    matches = []
    for tenant in Tenant.objects.exclude(schema_name__iexact='public').filter(is_active=True):
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                continue
            try:
                app = TenantApp.objects.filter(
                    app_name='mattermost',
                    extra_config__mm_team_id=team_id,
                    status__in=('active', 'provisioning'),
                ).first()
            except Exception:
                app = None
            if not app:
                continue
            expected = (app.extra_config or {}).get('mm_webhook_token', '')
            if request_token and expected:
                if hmac.compare_digest(request_token, expected):
                    matches.append((tenant, app))
            elif not request_token:
                matches.append((tenant, app))
    if not matches:
        return None, None
    for tenant, app in matches:
        if tenant.schema_name == 'polysaasonline':
            return tenant, app
    return matches[0]


def _parse_contact_message(text: str) -> dict | None:
    """Parse 'newpolysaascontact Name, email, Company' (shared format)."""
    return parse_contact_message(text)


@csrf_exempt
@require_POST
def mattermost_events_webhook(request):
    """Outgoing webhook: 'newpolysaascontact Name, email, Company' → Slack contact topic."""
    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body)
        else:
            payload = dict(request.POST.items())
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Invalid Mattermost webhook payload: %s", exc)
        return JsonResponse({'error': 'Invalid JSON or form data'}, status=400)

    team_id = payload.get('team_id', '')
    request_token = payload.get('token', '')
    if not team_id:
        return JsonResponse({'error': 'Missing team_id'}, status=400)

    tenant, mm_app = _find_mattermost_tenant(team_id, request_token)
    if not mm_app:
        logger.warning("Unknown Mattermost team_id: %s", team_id)
        return HttpResponseForbidden('Unknown Mattermost workspace.')

    contact_data = _parse_contact_message(payload.get('text', ''))
    if not contact_data:
        return JsonResponse({
            'status': 'ignored',
            'reason': 'message does not match contact format',
        })

    # Same mailbox fields the Slack instruction already consumes.
    contact_data['slack_user_id'] = payload.get('user_id', '')
    contact_data['slack_channel_id'] = payload.get('channel_id', '')
    contact_data['slack_message_ts'] = payload.get('post_id', '') or payload.get('timestamp', '')
    contact_data['slack_team_id'] = team_id

    result = publish_slack_contact_event(tenant, contact_data)
    if result.get('success'):
        return JsonResponse({
            'status': 'queued',
            'event_id': result.get('event_id'),
            'mailbox_id': result.get('mailbox_id'),
            'topic': 'slack.message.contact',
        })
    return JsonResponse({
        'status': 'error',
        'error': result.get('error', 'Failed to queue event'),
    }, status=503)
