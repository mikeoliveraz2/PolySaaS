# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Slack → Odoo Contact Creation — 2026-09-06

"""Slack Events API webhook endpoint for contact creation from messages."""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import time

from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from dose.models import Tenant, TenantApp
from dose.tenant_app_lookup import tenant_schema_search_path
from dose.webhook_events import publish_slack_contact_event


MAX_AGE_SECONDS = 300
CONTACT_PATTERN = re.compile(
    r'^New contact:\s*([^,]+),\s*([^,]+@[^,]+\.[^,]+),\s*(.+)$',
    re.IGNORECASE
)


def _find_slack_tenant(team_id: str):
    """Find a tenant with an active Slack TenantApp matching the given team_id."""
    for tenant in Tenant.objects.exclude(schema_name__iexact='public').filter(is_active=True):
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                continue
            try:
                app = TenantApp.objects.filter(
                    app_name='slack',
                    extra_config__slack_team_id=team_id,
                    status__in=('active', 'provisioning'),
                ).first()
            except Exception:
                app = None
            if app:
                return tenant, app
    return None, None


def _verify_slack_signature(signing_secret: str, timestamp: str, raw_body: bytes, signature: str) -> bool:
    """Verify a Slack request signature per Slack's signed-secret scheme."""
    if not signature or not signature.startswith('v0='):
        return False
    try:
        ts = int(timestamp)
    except (ValueError, TypeError):
        return False
    if abs(int(time.time()) - ts) > MAX_AGE_SECONDS:
        return False
    base = f'v0:{timestamp}:'.encode() + raw_body
    expected = hmac.new(signing_secret.encode(), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f'v0={expected}', signature)


def _parse_contact_message(text: str) -> dict | None:
    """
    Parse contact format: 'New contact: Name, email, Company'
    Returns dict with name, email, company or None if format doesn't match.
    """
    match = CONTACT_PATTERN.match(text.strip())
    if not match:
        return None
    
    name = match.group(1).strip()
    email = match.group(2).strip()
    company = match.group(3).strip()
    
    if not name or not email or not company:
        return None
    
    return {
        'name': name[:100],  # Odoo res.partner.name limit
        'email': email[:100],
        'company': company[:100],
    }


@csrf_exempt
@require_POST
def slack_events_webhook(request):
    """
    Slack Events API endpoint for message.channels subscription.
    
    Handles:
    - URL verification challenge
    - message.channels events with contact creation format
    """
    raw_body = request.body
    timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
    signature = request.headers.get('X-Slack-Signature', '')
    
    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Handle URL verification challenge
    if payload.get('type') == 'url_verification':
        challenge = payload.get('challenge', '')
        return JsonResponse({'challenge': challenge})
    
    # Verify signature for all other events
    if payload.get('type') != 'url_verification':
        team_id = payload.get('team_id', '')
        tenant, slack_app = _find_slack_tenant(team_id)
        
        if not slack_app:
            return HttpResponseForbidden('Unknown Slack workspace.')
        
        signing_secret = slack_app.extra_config.get('signing_secret', '')
        if not signing_secret:
            return HttpResponseForbidden('Slack signing secret not configured.')
        
        if not _verify_slack_signature(signing_secret, timestamp, raw_body, signature):
            return HttpResponseForbidden('Invalid Slack signature.')
    
    # Handle message events
    if payload.get('type') == 'event_callback':
        event = payload.get('event', {})
        
        # Only process channel messages (not DMs, not bot messages)
        if event.get('type') != 'message':
            return JsonResponse({'status': 'ignored', 'reason': 'not a message event'})
        
        if event.get('subtype'):  # Ignore message edits, deletes, etc.
            return JsonResponse({'status': 'ignored', 'reason': 'message subtype not supported'})
        
        if event.get('bot_id'):  # Ignore bot messages
            return JsonResponse({'status': 'ignored', 'reason': 'bot message'})
        
        # Parse contact format
        text = event.get('text', '')
        contact_data = _parse_contact_message(text)
        
        if not contact_data:
            return JsonResponse({'status': 'ignored', 'reason': 'message does not match contact format'})
        
        # Enrich with Slack event metadata
        contact_data['slack_user_id'] = event.get('user', '')
        contact_data['slack_channel_id'] = event.get('channel', '')
        contact_data['slack_message_ts'] = event.get('ts', '')
        contact_data['slack_team_id'] = payload.get('team_id', '')
        
        # Publish to mailbox
        result = publish_slack_contact_event(tenant, contact_data)
        
        if result.get('success'):
            return JsonResponse({
                'status': 'queued',
                'event_id': result.get('event_id'),
                'mailbox_id': result.get('mailbox_id'),
            })
        else:
            return JsonResponse({
                'status': 'error',
                'error': result.get('error', 'Failed to queue event'),
            }, status=503)
    
    return JsonResponse({'status': 'ignored', 'reason': 'unsupported event type'})
