"""
PolySaaS Mattermost Bot — WebSocket-driven AI peers dispatcher.

Peer roster:
  @grok / @supergrok  → xAI Grok        (BOT_TOKEN_SUPERGROK + XAI_API_KEY)
  @gemini / @gem      → Google Gemini   (BOT_TOKEN_GEM + GEMINI_API_KEY)
  @cc                 → Cursor Claude   (BOT_TOKEN_CC + ANTHROPIC_API_KEY)
  @wsc                → Windsurf Claude (BOT_TOKEN_WSC + ANTHROPIC_API_KEY)
  @kimi               → Moonshot Kimi   (BOT_TOKEN_KIMI + KIMI_API_KEY)

Routing rules:
  @<peer>   → only that peer responds
  @anyone   → all ACTIVE peers respond (those with both bot token + API key configured)
  no tag    → silence

Each peer posts to Mattermost using its OWN bot account token — messages appear
as real verified bot users, not overridden webhooks.

Run via:
    python manage.py run_mattermost_bot

NOTE: mattermostdriver's init_websocket callback is SYNCHRONOUS.
      Never wrap this bot in asyncio.run() — use threading for API calls.
"""
import importlib
import json
import logging
import threading

import requests as _requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Peer table — single source of truth for all AI peers
# ---------------------------------------------------------------------------
# Keys in PEERS are the @mention names users type in Mattermost.
# 'aliases' lists alternate trigger words that route to the same peer.
# 'mm_username' is the actual Mattermost bot account username.
# 'bot_token_key' is the Django settings attribute holding that bot's MM token.
# 'api_key_key'   is the Django settings attribute holding the LLM API key.
# 'router'        is the dotted Python module path for the LLM router.

PEERS = {
    'grok': {
        'aliases': ['supergrok'],
        'mm_username': 'supergrok',
        'bot_token_key': 'BOT_TOKEN_SUPERGROK',
        'api_key_key': 'XAI_API_KEY',
        'router': 'dose.mattermost_bot.routers.grok_router',
    },
    'gemini': {
        'aliases': ['gem'],
        'mm_username': 'gem',
        'bot_token_key': 'BOT_TOKEN_GEM',
        'api_key_key': 'GEMINI_API_KEY',
        'router': 'dose.mattermost_bot.routers.gemini_router',
    },
    'cc': {
        'aliases': [],
        'mm_username': 'cc',
        'bot_token_key': 'BOT_TOKEN_CC',
        'api_key_key': 'ANTHROPIC_API_KEY',
        'router': 'dose.mattermost_bot.routers.cc_router',
    },
    'wsc': {
        'aliases': [],
        'mm_username': 'wsc',
        'bot_token_key': 'BOT_TOKEN_WSC',
        'api_key_key': 'ANTHROPIC_API_KEY',
        'router': 'dose.mattermost_bot.routers.wsc_router',
    },
    'kimi': {
        'aliases': [],
        'mm_username': 'kimi',
        'bot_token_key': 'BOT_TOKEN_KIMI',
        'api_key_key': 'KIMI_API_KEY',
        'router': 'dose.mattermost_bot.routers.kimi_router',
    },
}

# Build reverse alias lookup  {alias: canonical_key}
_ALIAS_MAP: dict = {}
for _key, _peer in PEERS.items():
    _ALIAS_MAP[_key] = _key
    for _alias in _peer.get('aliases', []):
        _ALIAS_MAP[_alias] = _key

# Canonical set of all mm_usernames (for echo protection)
_BOT_USERNAMES = {p['mm_username'] for p in PEERS.values()}


def _mm_base_url() -> str:
    return getattr(settings, 'MATTERMOST_URL', 'https://polysaas-mattermost.onrender.com').rstrip('/')


def _active_peers() -> list:
    """Return canonical peer keys whose bot_token AND api_key are both configured."""
    active = []
    seen = set()
    for key, peer in PEERS.items():
        if key in seen:
            continue
        tok = getattr(settings, peer['bot_token_key'], '')
        api = getattr(settings, peer['api_key_key'], '')
        if tok and api:
            active.append(key)
            seen.add(key)
    return active


def _post_as_peer(peer_key: str, channel_id: str, message: str, root_id: str):
    """Post a message to Mattermost using the peer's own bot token."""
    peer = PEERS[peer_key]
    token = getattr(settings, peer['bot_token_key'], '')
    if not token:
        logger.warning("[MM Bot] No token for peer %s — cannot post", peer_key)
        return
    payload = {'channel_id': channel_id, 'message': message}
    if root_id:
        payload['root_id'] = root_id
    try:
        resp = _requests.post(
            f"{_mm_base_url()}/api/v4/posts",
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("[MM Bot] %s posted (%d chars)", peer_key, len(message))
    except Exception as exc:
        logger.error("[MM Bot] Post failed for %s: %s", peer_key, exc)


# ---------------------------------------------------------------------------
# Bot class
# ---------------------------------------------------------------------------

class PolySaaSAIPeersBot:
    """
    Single persistent WebSocket listener.
    Uses mattermostdriver (sync) — do NOT wrap in asyncio.run().
    Each peer posts its own response via its own Mattermost token.
    """

    def __init__(self):
        from mattermostdriver import Driver

        mm_url = _mm_base_url()
        host = mm_url.replace('https://', '').replace('http://', '')
        scheme = 'https' if mm_url.startswith('https') else 'http'
        port = 443 if scheme == 'https' else 80

        listen_token = (
            getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '') or
            getattr(settings, 'MATTERMOST_BOT_TOKEN', '')
        )

        self.driver = Driver({
            'url': host,
            'port': port,
            'scheme': scheme,
            'token': listen_token,
            'keepalive': True,
            'connect_timeout': 30,
        })
        self._bot_user_ids: set = set()
        self._processed_posts: set = set()

    def start(self):
        self.driver.login()
        me = self.driver.users.get_user('me')
        self._bot_user_ids.add(me['id'])
        logger.info("[MM Bot] Listener connected as @%s", me.get('username'))
        self._register_peer_ids()
        active = _active_peers()
        logger.info("[MM Bot] Active peers: %s", active)
        logger.info("[MM Bot] Listening — %s | @anyone", ' | '.join(f'@{k}' for k in active))
        self.driver.init_websocket(self._on_event)   # blocking

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def _on_event(self, raw):
        try:
            msg = json.loads(raw) if isinstance(raw, str) else raw
            if msg.get('event') != 'posted':
                return
            post_raw = msg.get('data', {}).get('post', '{}')
            post = json.loads(post_raw) if isinstance(post_raw, str) else post_raw
            self._dispatch(post)
        except Exception as exc:
            logger.error("[MM Bot] Event error: %s", exc)

    def _dispatch(self, post: dict):
        post_id = post.get('id', '')
        user_id = post.get('user_id', '')
        text = post.get('message', '').strip()
        channel_id = post.get('channel_id', '')

        # Deduplicate
        if post_id and post_id in self._processed_posts:
            return
        if post_id:
            self._processed_posts.add(post_id)
            if len(self._processed_posts) > 500:
                self._processed_posts.clear()

        # Echo protection
        if user_id in self._bot_user_ids:
            return
        sender = post.get('props', {}).get('override_username', '')
        if not sender:
            try:
                sender = self.driver.users.get_user(user_id).get('username', '')
            except Exception:
                sender = ''
        if sender.lower() in _BOT_USERNAMES:
            return

        # Routing
        lower = text.lower()
        if '@anyone' in lower:
            target_peers = _active_peers()
        else:
            seen: set = set()
            target_peers = []
            for token_word, canonical in _ALIAS_MAP.items():
                if f'@{token_word}' in lower and canonical not in seen:
                    target_peers.append(canonical)
                    seen.add(canonical)

        if not target_peers:
            return

        logger.info("[MM Bot] '%s' → %s", text[:60], target_peers)
        root_id = post.get('root_id') or post_id
        for peer_key in target_peers:
            threading.Thread(
                target=self._call_and_post,
                args=(peer_key, text, channel_id, root_id),
                daemon=True,
            ).start()

    # ------------------------------------------------------------------
    # Router dispatch
    # ------------------------------------------------------------------

    def _call_and_post(self, peer_key: str, text: str, channel_id: str, root_id: str):
        peer = PEERS[peer_key]
        try:
            router = importlib.import_module(peer['router'])
            response = router.handle(text, '', channel_id)
        except Exception as exc:
            logger.error("[MM Bot] Router %s error: %s", peer_key, exc)
            response = f"⚠️ {peer['mm_username'].capitalize()} is unavailable right now."
        _post_as_peer(peer_key, channel_id, response, root_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _register_peer_ids(self):
        for peer in PEERS.values():
            try:
                u = self.driver.users.get_user_by_username(peer['mm_username'])
                if u and u.get('id'):
                    self._bot_user_ids.add(u['id'])
                    logger.debug("[MM Bot] Registered bot id %s (@%s)", u['id'], peer['mm_username'])
            except Exception:
                pass


PolySaaSMattermostBot = PolySaaSAIPeersBot
