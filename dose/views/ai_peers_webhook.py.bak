"""
Mattermost outgoing webhook handler for AI as Peers.

Mattermost fires an outgoing webhook when a configured trigger word appears in
channel traffic. This view identifies mentioned peers and dispatches them to
the AI peer service.

The webhook returns 200 immediately — the AI response is posted back to the
channel asynchronously via the Mattermost API as the matching bot identity.
"""
import json
import logging
import re
import threading
import time
import requests

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from dose.services.ai_peer_service import handle_mention, PEER_REGISTRY

logger = logging.getLogger(__name__)

MENTION_PATTERN = re.compile(r'[#@](\w+)')

_peers_loaded = False
_processed_posts = set()
_hook_tokens_cache = {'tokens': set(), 'ts': 0.0}

# Channels where every message broadcasts to all active peers (no @mention needed).
# Use Mattermost channel *names* (not IDs).
BROADCAST_CHANNELS = {'town-square'}

PEER_SPECS = [
    {
        'username': 'github',
        'display_name': 'GitHub',
        'token_setting': 'BOT_TOKEN_GITHUB',
        'provider_setting': 'AI_PEER_PROVIDER_GITHUB',
        'default_provider': 'anthropic',
        'persona': (
            'You are GitHub, the repository peer for mikeoliveraz2/PolySaaS. '
            'Answer questions about the codebase, branches, PRs, and project structure.'
        ),
        'aliases': [],
    },
    {
        'username': 'copilot',
        'display_name': 'Copilot',
        'token_setting': 'BOT_TOKEN_COPILOT',
        'provider_setting': 'AI_PEER_PROVIDER_COPILOT',
        'default_provider': 'anthropic',
        'persona': 'You are Copilot, an engineering-focused AI peer. Prioritize code clarity, implementation detail, and actionable next steps.',
        'aliases': [],
    },
    {
        'username': 'cursor',
        'display_name': 'Cursor',
        'token_setting': 'BOT_TOKEN_CURSOR',
        'provider_setting': 'AI_PEER_PROVIDER_CURSOR',
        'default_provider': 'anthropic',
        'persona': 'You are Cursor, a pragmatic coding peer focused on direct implementation, debugging, and repo-aware iteration.',
        'aliases': ['cc'],
        'fallback_token_settings': ['BOT_TOKEN_CC'],
    },
    {
        'username': 'grok',
        'display_name': 'Grok',
        'token_setting': 'BOT_TOKEN_GROK',
        'provider_setting': 'AI_PEER_PROVIDER_GROK',
        'default_provider': 'xai',
        'persona': 'You are Grok, a direct AI peer focused on fast synthesis, candid tradeoffs, and decisive recommendations.',
        'aliases': ['supergrok'],
        'fallback_token_settings': ['BOT_TOKEN_SUPERGROK'],
    },
    {
        'username': 'router',
        'display_name': 'Router',
        'token_setting': 'BOT_TOKEN_ROUTER',
        'provider_setting': 'AI_PEER_PROVIDER_ROUTER',
        'default_provider': 'anthropic',
        'persona': 'You are Router, the orchestration peer. Your job is to clarify the request, decide which peer should respond, and when useful explicitly hand work to other AI peers.',
        'aliases': [],
    },
    {
        'username': 'openclaw',
        'display_name': 'OpenClaw',
        'token_setting': 'BOT_TOKEN_OPENCLAW',
        'provider_setting': 'AI_PEER_PROVIDER_OPENCLAW',
        'default_provider': 'anthropic',
        'persona': 'You are OpenClaw, an open-systems AI peer focused on extensibility, interoperability, and self-hostable workflows.',
        'aliases': ['opeclaw'],
    },
    {
        'username': 'gemini',
        'display_name': 'Gemini',
        'token_setting': 'BOT_TOKEN_GEMINI',
        'provider_setting': 'AI_PEER_PROVIDER_GEMINI',
        'default_provider': 'gemini',
        'persona': 'You are Gemini, a synthesis-focused AI peer powered by Google Gemini. You excel at multi-step reasoning, creative thinking, and broad knowledge synthesis.',
        'aliases': ['gem'],
        'fallback_token_settings': ['BOT_TOKEN_GEM'],
    },
    {
        'username': 'windsurf',
        'display_name': 'Windsurf',
        'token_setting': 'BOT_TOKEN_WINDSURF',
        'provider_setting': 'AI_PEER_PROVIDER_WINDSURF',
        'default_provider': 'windsurf',
        'persona': 'You are Windsurf, an AI peer specialising in software engineering, agentic coding workflows, and developer productivity on the PolySaaS platform.',
        'aliases': ['ws'],
    },
]


def _first_setting(*names):
    for name in names:
        value = getattr(settings, name, '')
        if value:
            return value
    return ''


def _peer_provider(spec):
    provider = getattr(settings, spec['provider_setting'], spec['default_provider'])
    return (provider or spec['default_provider']).strip().lower()


def _available_peer_tags(specs):
    tags = []
    for spec in specs:
        tags.append(f"#{spec['username']}")
        for alias in spec.get('aliases', []):
            tags.append(f"#{alias}")
    return ', '.join(dict.fromkeys(tags))


def _ensure_peers_loaded():
    """
    Lazily register AI peer identities from settings on first webhook call.
    Bot tokens must be set in settings for the peers you want enabled.
    """
    global _peers_loaded
    # We allow re-loading if we detect tokens are missing but exist in settings
    from django.conf import settings
    from dose.services.ai_peer_service import register_peer, PEER_REGISTRY

    if _peers_loaded and PEER_REGISTRY:
        return
    
    _peers_loaded = True

    polysaas_context = (
        "You are an AI peer collaborating in a Mattermost channel with humans "
        "(MO = Mike Oliver, founder; Shela = co-developer/business strategist) "
        "and other AI agents on the PolySaaS platform.\n\n"
        "PolySaaS is a multi-tenant SaaS orchestration platform that bundles "
        "open-source apps (Odoo, WordPress, Nextcloud, Mattermost, Liferay, Dolibarr) "
        "into subscription tiers:\n"
        "- PolySaaS-1 ($26/mo): 1 app\n"
        "- PolySaaS-3 ($49/mo): 3 apps incl. WordPress\n"
        "- PolySaaS-Unlimited ($99/mo): any number of apps + metered storage\n\n"
        "Key architecture: Django/DOSE passthrough proxy intercepts HTTP traffic, "
        "Instructions trigger Atomic Services, POST events publish to GCP Pub/Sub topics, "
        "PostgreSQL schema-per-tenant isolation.\n\n"
        "The team is preparing for a $15K SAFE raise and Wefunder community round. "
        "AI as Peers (this feature) is a key differentiator — multiple AI models "
        "collaborating visibly with humans in Mattermost channels.\n\n"
        "Be concise, helpful, and collaborative. Keep responses under 150 words unless "
        f"asked for detail. You can mention other peers with {_available_peer_tags(PEER_SPECS)}."
    )

    admin_fallback_token = getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '')

    PEER_REGISTRY.clear()
    for spec in PEER_SPECS:
        token_names = [spec['token_setting'], *spec.get('fallback_token_settings', [])]
        bot_token = _first_setting(*token_names)
        if not bot_token and admin_fallback_token:
            bot_token = admin_fallback_token
            logger.warning(
                "AI peer @%s missing %s; using MATTERMOST_ADMIN_TOKEN fallback",
                spec['username'],
                '/'.join(token_names),
            )
        if not bot_token:
            continue

        provider = _peer_provider(spec)
        register_peer(
            spec['username'],
            spec['display_name'],
            provider,
            bot_token,
            system_prompt=(
                f"{spec['persona']} {polysaas_context}"
            ),
            aliases=spec.get('aliases', []),
        )


def _post_dispatch_ack(peer_username: str, channel_id: str, post_id: str, trigger_text: str):
    """Post a short diagnostic ack as the target peer before LLM processing."""
    peer = PEER_REGISTRY.get((peer_username or '').lower())
    if not peer:
        return

    bot_token = peer.get('bot_token', '')
    if not bot_token:
        return

    mm_url = (getattr(settings, 'MATTERMOST_URL', '') or '').rstrip('/')
    if not mm_url:
        return

    preview = (trigger_text or '').strip().replace('\n', ' ')
    if len(preview) > 80:
        preview = preview[:77] + '...'

    payload = {
        'channel_id': channel_id,
        'message': f"[diag] mention received, processing: {preview}",
    }
    if post_id:
        payload['root_id'] = post_id

    try:
        requests.post(
            f"{mm_url}/api/v4/posts",
            headers={
                'Authorization': f"Bearer {bot_token}",
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=10,
        )
    except Exception as exc:
        logger.warning("AI peers webhook ack post failed for @%s: %s", peer_username, exc)


def _get_valid_webhook_tokens() -> set:
    """Return accepted webhook tokens from settings and Mattermost outgoing hooks."""
    raw = (getattr(settings, 'AI_PEERS_WEBHOOK_TOKEN', '') or '').strip()
    static_tokens = {t.strip() for t in raw.split(',') if t.strip()}

    # Cache Mattermost hook tokens briefly to avoid API calls on every message.
    now = time.time()
    if now - _hook_tokens_cache.get('ts', 0.0) < 60:
        return static_tokens | set(_hook_tokens_cache.get('tokens', set()))

    mm_url = (getattr(settings, 'MATTERMOST_URL', '') or '').rstrip('/')
    admin_token = (getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '') or '').strip()
    if not mm_url or not admin_token:
        _hook_tokens_cache['tokens'] = set()
        _hook_tokens_cache['ts'] = now
        return static_tokens

    dynamic_tokens = set()
    try:
        resp = requests.get(
            f"{mm_url}/api/v4/hooks/outgoing",
            headers={
                'Authorization': f"Bearer {admin_token}",
                'Content-Type': 'application/json',
            },
            timeout=15,
        )
        if resp.status_code == 200:
            payload = resp.json()
            hooks = (
                (payload.get('outgoing_webhooks') or payload.get('hooks') or [])
                if isinstance(payload, dict)
                else (payload or [])
            )
            for hook in hooks:
                tok = (hook.get('token') or '').strip()
                if tok:
                    dynamic_tokens.add(tok)
        else:
            logger.warning("Failed to fetch Mattermost outgoing hooks for token validation: %s", resp.status_code)
    except Exception as exc:
        logger.warning("Webhook token refresh failed: %s", exc)

    _hook_tokens_cache['tokens'] = dynamic_tokens
    _hook_tokens_cache['ts'] = now
    return static_tokens | dynamic_tokens


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
    if webhook_token:
        valid_tokens = _get_valid_webhook_tokens()
        if incoming_token not in valid_tokens:
            enforce = bool(getattr(settings, 'AI_PEERS_ENFORCE_WEBHOOK_TOKEN', False))
            logger.warning(
                "AI peers webhook: token mismatch for incoming webhook (enforce=%s)",
                enforce,
            )
            if enforce:
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

    # Broadcast to all active peers when no specific peer is mentioned
    # and the channel is in the broadcast list — the core "AI as a Service" demo.
    if not mentioned_peers:
        channel_name = data.get('channel_name', '')
        sender = data.get('user_name', '')
        bot_usernames = {s['username'].lower() for s in PEER_SPECS}
        bot_usernames.update(a.lower() for s in PEER_SPECS for a in s.get('aliases', []))
        if sender.lower() in bot_usernames:
            # Message is from one of our own bots — skip to prevent echo loops.
            return JsonResponse({'status': 'bot_message_skipped'})
        if channel_name in BROADCAST_CHANNELS:
            mentioned_peers = list(PEER_REGISTRY.keys())
            # Deduplicate (aliases point to same peer record)
            seen_tokens = set()
            deduped = []
            for p in mentioned_peers:
                token = PEER_REGISTRY[p].get('bot_token', '')
                if token not in seen_tokens:
                    seen_tokens.add(token)
                    deduped.append(p)
            mentioned_peers = deduped
        if not mentioned_peers:
            return JsonResponse({'status': 'no_peers_mentioned', 'available': list(PEER_REGISTRY.keys())})

    for peer_username in mentioned_peers:
        if bool(getattr(settings, 'AI_PEERS_DEBUG_ACK', True)):
            _post_dispatch_ack(peer_username, channel_id, post_id, text)
        thread = threading.Thread(
            target=handle_mention,
            args=(peer_username, channel_id, text, user_name, post_id),
            daemon=True,
        )
        thread.start()
        logger.info("Dispatched AI peer @%s for channel %s (by @%s)",
                     peer_username, channel_id, user_name)

    return JsonResponse({'status': 'dispatched', 'peers': mentioned_peers})
