"""
PolySaaS Mattermost Bot — WebSocket-driven AI peers dispatcher.

Routing rules:
  @grok      → only Grok responds (xAI API)
  @gemini    → only Gemini responds (Google Gemini API)
  @windsurf  → only Windsurf responds
  @anyone    → all active peers respond (broadcast)
  no tag     → silence (bot does not respond)

Each response is posted under the AI peer's visual identity via
override_username / override_icon_url.

Run via:
    python manage.py run_mattermost_bot

NOTE: mattermostdriver's init_websocket callback is SYNCHRONOUS.
      Never wrap this bot in asyncio.run() — use threading for API calls.
"""
import json
import logging
import threading

logger = logging.getLogger(__name__)

BOT_NAMES = {'grok', 'gemini', 'windsurf'}

ROUTERS = {
    'grok': 'dose.mattermost_bot.routers.grok_router',
    'gemini': 'dose.mattermost_bot.routers.gemini_router',
    'windsurf': 'dose.mattermost_bot.routers.windsurf_router',
}

PEER_ICONS = {
    'grok': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/XAI_Logo.svg/120px-XAI_Logo.svg.png',
    'gemini': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Google_Gemini_logo.svg/120px-Google_Gemini_logo.svg.png',
    'windsurf': 'https://windsurf.com/favicon.ico',
}


class PolySaaSAIPeersBot:
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
        """Login, register bot IDs for echo-filtering, then block on WebSocket."""
        self.driver.login()
        me = self.driver.users.get_user('me')
        self._bot_user_ids.add(me['id'])
        logger.info("[MM Bot] Connected as @%s (id=%s)", me.get('username'), me.get('id'))
        self._register_peer_ids()
        logger.info("[MM Bot] Listening — @grok | @gemini | @windsurf | @anyone")
        self.driver.init_websocket(self._on_event)   # blocking

    # ------------------------------------------------------------------
    # Event handling (synchronous — called directly by mattermostdriver)
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
            logger.error("[MM Bot] Event handler error: %s", exc)

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

        # Echo protection — ignore posts from any bot account
        if user_id in self._bot_user_ids:
            return
        sender = post.get('props', {}).get('override_username', '')
        if not sender:
            try:
                sender = self.driver.users.get_user(user_id).get('username', '')
            except Exception:
                sender = ''
        if sender.lower() in BOT_NAMES:
            return

        # Routing
        lower = text.lower()
        if '@anyone' in lower:
            peers = list(BOT_NAMES)
        else:
            peers = [p for p in BOT_NAMES if f'@{p}' in lower]

        if not peers:
            return   # no mention — stay silent

        logger.info("[MM Bot] %s → dispatching to %s", text[:60], peers)
        for peer in peers:
            threading.Thread(
                target=self._call_and_post,
                args=(peer, text, channel_id, post.get('root_id') or post_id),
                daemon=True,
            ).start()

    # ------------------------------------------------------------------
    # Router dispatch + posting
    # ------------------------------------------------------------------

    def _call_and_post(self, peer: str, text: str, channel_id: str, root_id: str):
        """Call the peer router in a thread, then post the response to the channel."""
        try:
            import importlib
            router = importlib.import_module(ROUTERS[peer])
            response = router.handle(text, '', channel_id)
        except Exception as exc:
            logger.error("[MM Bot] Router %s failed: %s", peer, exc)
            response = f"⚠️ {peer.capitalize()} is unavailable right now."

        try:
            self.driver.posts.create_post({
                'channel_id': channel_id,
                'message': response,
                'root_id': root_id,
                'props': {
                    'override_username': peer.capitalize(),
                    'override_icon_url': PEER_ICONS.get(peer, ''),
                    'from_webhook': 'true',
                },
            })
            logger.info("[MM Bot] Posted %s response (%d chars)", peer, len(response))
        except Exception as exc:
            logger.error("[MM Bot] Failed to post %s response: %s", peer, exc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _register_peer_ids(self):
        """Collect Mattermost user IDs for bot accounts to prevent echo loops."""
        for name in BOT_NAMES:
            try:
                u = self.driver.users.get_user_by_username(name)
                if u and u.get('id'):
                    self._bot_user_ids.add(u['id'])
                    logger.debug("[MM Bot] Registered peer id %s (@%s)", u['id'], name)
            except Exception:
                pass   # bot account not created yet — fine


# Keep old class name as alias for backwards compatibility
PolySaaSMattermostBot = PolySaaSAIPeersBot
