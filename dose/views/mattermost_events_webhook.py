"""
Mattermost Outgoing Webhook endpoint for contact/sale creation.

Receives Mattermost webhook POSTs, normalizes into canonical event schema,
and publishes to RabbitMQ for orchestration.

Parallel to slack_events_webhook.py but with Mattermost-specific auth and payload handling.
"""
from __future__ import annotations
import json
import logging
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from dose.mattermost.auth import verify_mattermost_token, find_mattermost_tenant
from dose.mattermost.normalizer import normalize_mattermost_webhook, get_routing_key

logger = logging.getLogger(__name__)


def _publish_mattermost_event(tenant, canonical_event: dict) -> dict:
    """
    Publish Mattermost event to RabbitMQ.
    
    Reuses SAME RabbitMQ infrastructure as Slack:
    - Same exchange (polysaas.events)
    - Same routing keys (contact.new, sale.new)
    - Same queues
    - Same consumers
    
    Args:
        tenant: Tenant model instance
        canonical_event: Normalized event dict
    
    Returns:
        Dict with success status and event details
    """
    from dose.models import WebhookMailbox
    from django.utils import timezone
    
    routing_key = get_routing_key(canonical_event)
    
    # Build envelope (same structure as Slack uses)
    envelope = {
        "event_key": canonical_event['event_type'],
        "action_path": f"/events/mattermost/{canonical_event['event_type']}",
        "source": "mattermost",
        "tenant_slug": tenant.slug,
        "payload": canonical_event,
        "timestamp": canonical_event['timestamp'],
        "routing_key": routing_key,
    }
    
    # Generate deterministic event_id
    import hashlib
    event_id_raw = f"mm_{canonical_event['metadata']['post_id']}_{canonical_event['timestamp']}"
    event_id = hashlib.sha256(event_id_raw.encode()).hexdigest()[:16]
    
    # Write to WebhookMailbox (same table as Slack)
    try:
        mailbox = WebhookMailbox.objects.create(
            tenant=tenant,
            event_id=event_id,
            event_key=canonical_event['event_type'],
            routing_key=routing_key,
            payload=envelope,
            received_at=timezone.now(),
            status='pending',
        )
        
        logger.info(
            f"[Mattermost] Event {event_id} queued: {canonical_event['event_type']} "
            f"for tenant {tenant.slug}"
        )
        
        return {
            'success': True,
            'event_id': event_id,
            'mailbox_id': mailbox.id,
            'routing_key': routing_key,
        }
        
    except Exception as e:
        logger.error(f"Failed to queue Mattermost event: {e}")
        return {
            'success': False,
            'error': str(e),
        }


@csrf_exempt
@require_POST
def mattermost_events_webhook(request):
    """
    Mattermost Outgoing Webhook endpoint.
    
    Handles:
    - Token verification (simpler than Slack's HMAC)
    - Payload normalization
    - Event publishing to RabbitMQ
    
    Mattermost Outgoing Webhook Format:
    {
        "token": "webhook_secret",
        "team_id": "team123",
        "team_domain": "polysaas",
        "channel_id": "channel123",
        "channel_name": "town-square",
        "timestamp": 1725678900,
        "user_id": "user123",
        "user_name": "michael.oliver",
        "post_id": "post123",
        "text": "New contact: Jane Doe, jane@acme.com, Acme Corp",
        "trigger_word": "New contact:"
    }
    
    Returns:
        JSON response with status
    """
    try:
        # Parse JSON body or form data
        if request.content_type == 'application/json':
            payload = json.loads(request.body)
        else:
            # Mattermost can send as form data
            payload = dict(request.POST.items())
        
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Invalid Mattermost webhook payload: {e}")
        return JsonResponse({'error': 'Invalid JSON or form data'}, status=400)
    
    # Extract team_id and token
    team_id = payload.get('team_id', '')
    request_token = payload.get('token', '')
    
    if not team_id:
        return JsonResponse({'error': 'Missing team_id'}, status=400)
    
    # Find tenant by team_id
    tenant, mm_app = find_mattermost_tenant(team_id)
    
    if not mm_app:
        logger.warning(f"Unknown Mattermost team_id: {team_id}")
        return HttpResponseForbidden('Unknown Mattermost workspace.')
    
    # Verify token
    expected_token = mm_app.extra_config.get('mm_webhook_token', '')
    if not verify_mattermost_token(request_token, expected_token):
        logger.warning(
            f"Invalid Mattermost webhook token for tenant {tenant.slug}, "
            f"team_id {team_id}"
        )
        return HttpResponseForbidden('Invalid webhook token.')
    
    # Normalize payload to canonical event schema
    canonical_event = normalize_mattermost_webhook(payload, tenant)
    
    if not canonical_event:
        # Message doesn't match any recognized format
        logger.debug(
            f"Mattermost message ignored (unrecognized format): {payload.get('text', '')}"
        )
        return JsonResponse({
            'status': 'ignored',
            'reason': 'message does not match contact or sale format'
        })
    
    # Publish to RabbitMQ (SAME infrastructure as Slack)
    result = _publish_mattermost_event(tenant, canonical_event)
    
    if result.get('success'):
        logger.info(
            f"[Mattermost] Successfully queued {canonical_event['event_type']} event "
            f"for tenant {tenant.slug}"
        )
        return JsonResponse({
            'status': 'queued',
            'event_id': result.get('event_id'),
            'mailbox_id': result.get('mailbox_id'),
            'routing_key': result.get('routing_key'),
        })
    else:
        logger.error(
            f"[Mattermost] Failed to queue event: {result.get('error')}"
        )
        return JsonResponse({
            'status': 'error',
            'error': result.get('error', 'Failed to queue event'),
        }, status=503)
