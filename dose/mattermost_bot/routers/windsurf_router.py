"""
Windsurf router -- Windsurf AI (api.windsurf.ai) peer for Mattermost.
Sync -- called from a threading.Thread in bot.py.
"""
import logging
import re
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

WINDSURF_API_URL = "https://api.windsurf.ai/v1/chat/completions"
WINDSURF_MODEL = "windsurf-swe-1"

_MENTION_RE = re.compile(r'@(?:windsurf|ws|anyone)\b', re.IGNORECASE)


def handle(message: str, user_id: str, channel_id: str) -> str:
    api_key = getattr(settings, 'WINDSURF_API_KEY', '')
    if not api_key:
        return "[Windsurf] Offline -- WINDSURF_API_KEY not configured."

    clean = _MENTION_RE.sub('', message).strip()
    if not clean:
        return (
            "Hi! I'm **Windsurf**, your agentic coding peer on PolySaaS. "
            "Tag **@windsurf** (or **@ws**) with a question."
        )

    model = getattr(settings, 'WINDSURF_MODEL', WINDSURF_MODEL)
    try:
        resp = requests.post(
            WINDSURF_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Windsurf, an AI peer specialising in software engineering "
                            "and agentic coding workflows, integrated into the PolySaaS "
                            "Mattermost workspace. PolySaaS is a multi-tenant SaaS orchestration "
                            "platform (Django/DOSE). "
                            "You collaborate with humans (MO = Mike Oliver; Shela = co-developer) "
                            "and other AI peers (@grok, @copilot, @github, @gemini, @cc, @wsc, @kimi). "
                            "Be concise and developer-focused. Use markdown. "
                            "Keep responses under 150 words unless asked for detail."
                        ),
                    },
                    {"role": "user", "content": clean},
                ],
                "temperature": 0.7,
                "max_tokens": 1500,
            },
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        logger.warning("[Windsurf] API timeout")
        return "[Windsurf] Thinking... (timeout -- try again)"
    except Exception as exc:
        logger.error("[Windsurf] API error: %s", exc)
        return f"[Windsurf] Error: {str(exc)[:120]}"
