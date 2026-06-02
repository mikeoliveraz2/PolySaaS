"""
CC router -- Cursor Claude (Anthropic Claude API).
Sync -- called from a threading.Thread in bot.py.
"""
import logging
import re
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-6"

_MENTION_RE = re.compile(r'@(?:cc|cursor|anyone)\b', re.IGNORECASE)


def handle(message: str, user_id: str, channel_id: str) -> str:
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        return "[CC] Offline -- ANTHROPIC_API_KEY not configured."

    clean = _MENTION_RE.sub('', message).strip()
    if not clean:
        return (
            "Hi! I'm **CC** (Cursor Claude), your pragmatic coding peer on PolySaaS. "
            "Tag **@cc** with a question."
        )

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
                    "You are CC (Cursor Claude), a pragmatic coding peer in the PolySaaS "
                    "Mattermost workspace, powered by Claude (Anthropic). PolySaaS is a "
                    "multi-tenant SaaS orchestration platform (Django/DOSE). "
                    "You collaborate with humans (MO = Mike Oliver; Shela = co-developer) "
                    "and other AI peers (@grok, @copilot, @github, @gemini, @wsc, @kimi, @windsurf). "
                    "Focus on direct implementation, debugging, and repo-aware iteration. "
                    "Be concise; use markdown. Keep responses under 150 words unless asked for detail."
                ),
                "messages": [{"role": "user", "content": clean}],
            },
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()['content'][0]['text']
    except requests.exceptions.Timeout:
        logger.warning("[CC] API timeout")
        return "[CC] Thinking... (timeout -- try again)"
    except Exception as exc:
        logger.error("[CC] API error: %s", exc)
        return f"[CC] Error: {str(exc)[:120]}"
