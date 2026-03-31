"""
Mattermost outgoing webhook handler for AI as Peers.

Mattermost fires an outgoing webhook when a trigger word (@cc, @supergrok)
appears in a channel message. This view receives that payload, identifies
which peer(s) were mentioned, and dispatches to the AI peer service.

The webhook returns 200 immediately — the AI response is posted back to
the channel asynchronously via the Mattermost API (as the bot user identity).
"""
import json
import logging
import re
import threading

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from dose.services.ai_peer_service import handle_mention, PEER_REGISTRY

logger = logging.getLogger(__name__)

MENTION_PATTERN = re.compile(r'@(\w+)')

_peers_loaded = False


def _ensure_peers_loaded():
    """
    Lazily register AI peer identities from env vars on first webhook call.
    Bot tokens must be set as BOT_TOKEN_CC / BOT_TOKEN_SUPERGROK in env.
    The management command setup_ai_peers creates these tokens in Mattermost.
    """
    global _peers_loaded
    if _peers_loaded:
        return
    _peers_loaded = True

    import os
    from dose.services.ai_peer_service import register_peer

    cc_token = os.environ.get('BOT_TOKEN_CC', '')
    if cc_token:
        register_peer('cc', 'CC (Claude Opus)', 'anthropic', cc_token)

    grok_token = os.environ.get('BOT_TOKEN_SUPERGROK', '')
    if grok_token:
        register_peer('supergrok', 'SuperGrok', 'xai', grok_token)


@csrf_exempt
@require_POST
def ai_peers_webhook(request):
    """
    Receive Mattermost outgoing webhook, dispatch to AI peer(s) in background.
    Returns 200 immediately so Mattermost doesn't retry.
    """
    _ensure_peers_loaded()

    webhook_token = getattr(settings, 'AI_PEERS_WEBHOOK_TOKEN', '')
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    incoming_token = data.get('token', '')
    if webhook_token and incoming_token != webhook_token:
        logger.warning("AI peers webhook: token mismatch")
        return JsonResponse({'error': 'Forbidden'}, status=403)

    text = data.get('text', '')
    channel_id = data.get('channel_id', '')
    post_id = data.get('post_id', '')
    user_name = data.get('user_name', '')

    if not text or not channel_id:
        return JsonResponse({'error': 'Missing text or channel_id'}, status=400)

    mentioned_peers = [
        m.group(1).lower()
        for m in MENTION_PATTERN.finditer(text)
        if m.group(1).lower() in PEER_REGISTRY
    ]

    if not mentioned_peers:
        return JsonResponse({'status': 'no_peers_mentioned'})

    for peer_username in mentioned_peers:
        thread = threading.Thread(
            target=handle_mention,
            args=(peer_username, channel_id, text, user_name, post_id),
            daemon=True,
        )
        thread.start()
        logger.info("Dispatched AI peer @%s for channel %s (by @%s)",
                     peer_username, channel_id, user_name)

    return JsonResponse({'status': 'dispatched', 'peers': mentioned_peers})
