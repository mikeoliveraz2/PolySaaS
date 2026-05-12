"""
CC router — Cursor Claude (Anthropic Claude API).
Sync — called from a threading.Thread in bot.py.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"


def handle(message: str, user_id: str, channel_id: str) -> str:
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        return "⚠️ CC is offline — ANTHROPIC_API_KEY not configured."

    clean = message.replace('@cc', '').replace('@CC', '').strip()
    if not clean:
        return "Hi! Ask me anything by tagging **@cc** followed by your question."

    try:
        resp = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": 1500,
                "system": (
                    "You are CC, an AI assistant powered by Claude (Anthropic). "
                    "You are integrated into PolySaaS as an AI Peer in a Mattermost team channel. "
                    "Be helpful, thoughtful, and concise. Use markdown where appropriate."
                ),
                "messages": [{"role": "user", "content": clean}],
            },
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()['content'][0]['text']
    except requests.exceptions.Timeout:
        logger.warning("[CC] API timeout")
        return "⚠️ CC is thinking... (timeout — try again)"
    except Exception as exc:
        logger.error("[CC] API error: %s", exc)
        return f"⚠️ CC hit an error: {str(exc)[:120]}"
