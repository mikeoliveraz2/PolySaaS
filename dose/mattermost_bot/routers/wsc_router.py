"""
WSC router -- Windsurf Claude (Anthropic Claude API via Windsurf identity).
Sync -- called from a threading.Thread in bot.py.
"""
import logging
import re
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-6"

_MENTION_RE = re.compile(r'@(?:wsc|anyone)\b', re.IGNORECASE)


def handle(message: str, user_id: str, channel_id: str) -> str:
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        return "[WSC] Offline -- ANTHROPIC_API_KEY not configured."

    clean = _MENTION_RE.sub('', message).strip()
    if not clean:
        return (
            "Hi! I'm **WSC** (Windsurf Claude), your developer productivity peer on PolySaaS. "
            "Tag **@wsc** with a question."
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
                    "You are WSC (Windsurf Claude), a developer productivity peer in the "
                    "PolySaaS Mattermost workspace, powered by Claude (Anthropic). "
                    "PolySaaS is a multi-tenant SaaS orchestration platform (Django/DOSE). "
                    "You collaborate with humans (MO = Mike Oliver; Shela = co-developer) "
                    "and other AI peers (@grok, @copilot, @github, @gemini, @cc, @kimi, @windsurf). "
                    "Be precise, technical, and developer-friendly. Use markdown. "
                    "Keep responses under 150 words unless asked for detail."
                ),
                "messages": [{"role": "user", "content": clean}],
            },
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()['content'][0]['text']
    except requests.exceptions.Timeout:
        logger.warning("[WSC] API timeout")
        return "[WSC] Thinking... (timeout -- try again)"
    except Exception as exc:
        logger.error("[WSC] API error: %s", exc)
        return f"[WSC] Error: {str(exc)[:120]}"
