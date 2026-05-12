"""
Windsurf router — stub for Windsurf AI integration.
Sync (no asyncio) — called from a threading.Thread in bot.py.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

WINDSURF_DISPLAY_NAME = "Windsurf"
WINDSURF_ICON_URL = "https://windsurf.com/favicon.ico"


def handle(message: str, user_id: str, channel_id: str) -> str:
    """Windsurf handler — calls API if key is set, otherwise returns stub."""
    api_key = getattr(settings, 'WINDSURF_API_KEY', '')
    clean = message.replace('@windsurf', '').replace('@Windsurf', '').strip()

    if not api_key:
        return (
            f"🌊 **Windsurf** received: _{clean[:150]}_\n\n"
            "*(Full Windsurf integration coming soon — WINDSURF_API_KEY not yet configured)*"
        )

    try:
        import requests
        resp = requests.post(
            "https://api.codeium.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "windsurf-1",
                "messages": [{"role": "user", "content": clean}],
                "temperature": 0.7,
                "max_tokens": 1500,
            },
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except Exception as exc:
        logger.error("[Windsurf] API error: %s", exc)
        return f"⚠️ Windsurf hit an error: {str(exc)[:120]}"
