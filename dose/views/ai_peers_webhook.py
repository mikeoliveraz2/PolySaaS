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

MENTION_PATTERN = re.compile(r'[#@](\w+)')

_peers_loaded = False
_processed_posts = set()


def _ensure_peers_loaded():
    """
    Lazily register AI peer identities from settings on first webhook call.
    Bot tokens must be set as BOT_TOKEN_CC / BOT_TOKEN_SUPERGROK in settings.
    """
    global _peers_loaded
    # We allow re-loading if we detect tokens are missing but exist in settings
    from django.conf import settings
    from dose.services.ai_peer_service import register_peer, PEER_REGISTRY

    cc_token = getattr(settings, 'BOT_TOKEN_CC', '')
    grok_token = getattr(settings, 'BOT_TOKEN_SUPERGROK', '')
    gem_token = getattr(settings, 'BOT_TOKEN_GEM', '')

    if _peers_loaded and 'cc' in PEER_REGISTRY and 'supergrok' in PEER_REGISTRY:
        return
    
    _peers_loaded = True

    polysaas_context = (
        "You are an AI peer collaborating in a Mattermost channel with humans "
        "(MO = Mike Oliver, founder; Shela = co-developer/business strategist) "
        "and other AI agents on the PolySaaS platform.\n\n"
        "PolySaaS is a multi-tenant SaaS orchestration platform that bundles "
        "open-source apps (Odoo, WordPress, Nextcloud, Mattermost, Liferay, Dolibarr) "
        "into subscription tiers:\n"
        "- PolySaaS-1 ($29.99/mo): 1 app\n"
        "- PolySaaS-3 ($79.99/mo): 3 apps incl. WordPress\n"
        "- PolySaaS-Unlimited ($199.99/mo): any number of apps + metered storage\n\n"
        "Key architecture: Django/DOSE passthrough proxy intercepts HTTP traffic, "
        "Instructions trigger Atomic Services, POST events publish to GCP Pub/Sub topics, "
        "PostgreSQL schema-per-tenant isolation.\n\n"
        "The team is preparing for a $15K SAFE raise and Wefunder community round. "
        "AI as Peers (this feature) is a key differentiator — multiple AI models "
        "collaborating visibly with humans in Mattermost channels.\n\n"
        "Be concise, helpful, and collaborative. Keep responses under 150 words unless "
        "asked for detail. You can mention other peers with #cc, #supergrok, or #gem."
    )

    if cc_token:
        register_peer('cc', 'CC (Claude)', 'anthropic', cc_token,
                       system_prompt=f"You are CC, powered by Anthropic Claude. {polysaas_context}")

    if grok_token:
        register_peer('supergrok', 'SuperGrok', 'xai', grok_token,
                       system_prompt=f"You are SuperGrok, powered by xAI Grok. {polysaas_context}")

    if gem_token:
        register_peer('gem', 'Gem (Gemini)', 'gemini', gem_token,
                       system_prompt=f"You are Gem, powered by Google Gemini. {polysaas_context}")


@csrf_exempt
@require_POST
def ai_peers_webhook(request):
    """
    Receive Mattermost outgoing webhook, dispatch to AI peer(s) in background.
    Returns 200 immediately so Mattermost doesn't retry.
    """
    print(f"[DEBUG] AI Peers Webhook hit: {request.method} {request.path}")
    print(f"[DEBUG] Request body: {request.body.decode('utf-8')}")
    _ensure_peers_loaded()

    webhook_token = getattr(settings, 'AI_PEERS_WEBHOOK_TOKEN', '')
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    incoming_token = data.get('token', '')
    if webhook_token and incoming_token != webhook_token:
        logger.warning(f"AI peers webhook: token mismatch. Expected '{webhook_token}', got '{incoming_token}'")
        return JsonResponse({'error': 'Forbidden'}, status=403)

    text = data.get('text', '')
    channel_id = data.get('channel_id', '')
    post_id = data.get('post_id', '')
    user_name = data.get('user_name', '')

    if not text or not channel_id:
        return JsonResponse({'error': 'Missing text or channel_id'}, status=400)

    if post_id:
        if post_id in _processed_posts:
            print(f"[DEBUG] Already processed post_id {post_id}, skipping.")
            return JsonResponse({'status': 'already_processed'})
        _processed_posts.add(post_id)
        # Keep the set small
        if len(_processed_posts) > 100:
            _processed_posts.pop()

    mentioned_peers = []
    for m in MENTION_PATTERN.finditer(text):
        peer_name = m.group(1).lower()
        print(f"[DEBUG] Found mention: @{peer_name}")
        if peer_name in PEER_REGISTRY:
            mentioned_peers.append(peer_name)
        else:
            print(f"[DEBUG] Peer @{peer_name} NOT in PEER_REGISTRY. Available: {list(PEER_REGISTRY.keys())}")

    if not mentioned_peers:
        return JsonResponse({'status': 'no_peers_mentioned', 'available': list(PEER_REGISTRY.keys())})

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
