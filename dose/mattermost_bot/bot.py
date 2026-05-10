"""
PolySaaS Mattermost Bot — WebSocket-driven AI peer dispatcher.

Connects to Mattermost via the mattermostdriver WebSocket API and listens
for posted events.  Dispatches to the existing ai_peer_service.py LLM router:

  - Message with @grok, @gemini, @windsurf → only that peer responds
  - Message in Town Square with no @mention → all active peers respond (broadcast)
  - Messages from bot accounts are silently ignored (no echo loops)

Run via:
    python manage.py run_mattermost_bot
"""
import json
import logging
import threading

logger = logging.getLogger(__name__)


class PolySaaSMattermostBot:
    """
    Single persistent WebSocket connection to Mattermost.
    Uses mattermostdriver (sync) — do NOT wrap in asyncio.run().
    """

    def __init__(self):
        from django.conf import settings
        from mattermostdriver import Driver

        mm_url = getattr(settings, 'MATTERMOST_URL', 'https://polysaas-mattermost.onrender.com')
        host = mm_url.replace('https://', '').replace('http://', '').rstrip('/')
        scheme = 'https' if mm_url.startswith('https') else 'http'
        port = 443 if scheme == 'https' else 80

        self.driver = Driver({
            'url': host,
            'port': port,
            'scheme': scheme,
            'token': getattr(settings, 'MATTERMOST_BOT_TOKEN', '') or
                     getattr(settings, 'MATTERMOST_ADMIN_TOKEN', ''),
            'keepalive': True,
            'connect_timeout': 30,
        })
        self._bot_user_ids: set = set()
        self._processed_posts: set = set()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self):
        """Login, collect bot user IDs for echo-filtering, then block on WebSocket."""
        self.driver.login()
        me = self.driver.users.get_user('me')
        self._bot_user_ids.add(me['id'])
        logger.info("[MM Bot] Connected as @%s (id=%s)", me.get('username'), me.get('id'))

        # Also register all peer bot user IDs so we never echo their posts.
        self._collect_bot_user_ids()

        logger.info("[MM Bot] Listening for events (broadcast + @mention routing)…")
        self.driver.init_websocket(self._on_event)   # blocking

    # ------------------------------------------------------------------
    # Event handling (called synchronously by mattermostdriver)
    # ------------------------------------------------------------------

    def _on_event(self, raw):
        try:
            msg = json.loads(raw) if isinstance(raw, str) else raw
            if msg.get('event') != 'posted':
                return
            post_raw = msg.get('data', {}).get('post', '{}')
            post = json.loads(post_raw) if isinstance(post_raw, str) else post_raw
            channel_name = msg.get('data', {}).get('channel_name', '')
            self._dispatch(post, channel_name)
        except Exception as exc:
            logger.error("[MM Bot] Event handler error: %s", exc)

    def _dispatch(self, post: dict, channel_name: str):
        from dose.views.ai_peers_webhook import (
            PEER_SPECS, BROADCAST_CHANNELS, MENTION_PATTERN, _ensure_peers_loaded,
        )
        from dose.services.ai_peer_service import handle_mention, PEER_REGISTRY

        _ensure_peers_loaded()

        post_id = post.get('id', '')
        user_id = post.get('user_id', '')
        text = post.get('message', '')
        channel_id = post.get('channel_id', '')

        # Deduplicate events
        if post_id and post_id in self._processed_posts:
            return
        if post_id:
            self._processed_posts.add(post_id)
            if len(self._processed_posts) > 500:
                self._processed_posts.clear()

        # Ignore posts from our own bot accounts
        if user_id in self._bot_user_ids:
            return

        # Resolve sender username for context
        user_name = post.get('props', {}).get('override_username', '')
        if not user_name:
            try:
                u = self.driver.users.get_user(user_id)
                user_name = u.get('username', user_id)
            except Exception:
                user_name = user_id

        # Also skip if sender username is one of our bot names
        bot_usernames = {s['username'].lower() for s in PEER_SPECS}
        bot_usernames.update(a.lower() for s in PEER_SPECS for a in s.get('aliases', []))
        if user_name.lower() in bot_usernames:
            return

        # --- routing logic ---
        mentioned_peers = []
        for m in MENTION_PATTERN.finditer(text):
            peer_name = m.group(1).lower()
            if peer_name in PEER_REGISTRY:
                mentioned_peers.append(peer_name)

        if not mentioned_peers:
            if channel_name not in BROADCAST_CHANNELS:
                return   # not a broadcast channel and no mention — ignore
            # Deduplicate by bot_token (aliases share same token)
            seen_tokens: set = set()
            for key, peer in PEER_REGISTRY.items():
                tok = peer.get('bot_token', '')
                if tok and tok not in seen_tokens:
                    seen_tokens.add(tok)
                    mentioned_peers.append(key)

        if not mentioned_peers:
            return

        logger.info("[MM Bot] Dispatching to %s for %r (channel=%s)", mentioned_peers, text[:60], channel_name)
        for peer_username in mentioned_peers:
            threading.Thread(
                target=handle_mention,
                args=(peer_username, channel_id, text, user_name, post_id),
                daemon=True,
            ).start()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _collect_bot_user_ids(self):
        """Fetch Mattermost user IDs for each configured bot so we can filter their posts."""
        from dose.views.ai_peers_webhook import PEER_SPECS
        for spec in PEER_SPECS:
            try:
                u = self.driver.users.get_user_by_username(spec['username'])
                if u and u.get('id'):
                    self._bot_user_ids.add(u['id'])
                    logger.debug("[MM Bot] Registered bot id %s (@%s)", u['id'], spec['username'])
            except Exception:
                pass   # bot account not created yet — fine
