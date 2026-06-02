"""
Grok router -- calls xAI API and returns the response text.
Sync (no asyncio) -- called from a threading.Thread in bot.py.
"""
import logging
import re
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GROK_API_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-3"

_MENTION_RE = re.compile(r'@(?:grok|supergrok|anyone)\b', re.IGNORECASE)

SYSTEM_PROMPT = (
    "You are Grok, a direct and witty AI peer built by xAI, integrated into "
    "the PolySaaS Mattermost workspace. PolySaaS is a multi-tenant SaaS "
    "orchestration platform (Django/DOSE) that bundles open-source apps "
    "(Mattermost, Odoo, Nextcloud, WordPress) for subscribers. "
    "You collaborate with humans (MO = Mike Oliver, founder; Shela = co-developer) "
    "and other AI peers (@copilot, @github, @gemini, @cc, @wsc, @kimi, @windsurf). "
    "Be concise and candid. Use markdown formatting where appropriate. "
    "Keep responses under 150 words unless asked for detail."
)


def handle(message: str, user_id: str, channel_id: str) -> str:
    """Call xAI Grok API. Returns response text or an error string."""
    api_key = getattr(settings, 'XAI_API_KEY', '')
    if not api_key:
        return "[Grok] I am temporarily unavailable -- XAI_API_KEY not configured."

    clean = _MENTION_RE.sub('', message).strip()
    if not clean:
        return (
            "Hi! I'm **Grok**, your xAI peer on PolySaaS. "
            "Tag **@grok** (or **@supergrok**) with a question."
        )

    try:
        resp = requests.post(
            GROK_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": GROK_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": clean},
                ],
                "temperature": 0.7,
                "max_tokens": 1500,
            },
            timeout=45,
        )
        if resp.status_code == 403:
            logger.warning("[Grok] xAI returned 403 -- credits or spend limit hit")
            return (
                "[Grok] I am temporarily unavailable because my xAI provider "
                "is out of credits or has hit a spend limit. Please retry shortly."
            )
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        logger.warning("[Grok] API timeout")
        return "[Grok] Thinking hard... (timeout -- try again)"
    except requests.exceptions.HTTPError:
        raise
    except Exception as exc:
        logger.error("[Grok] API error: %s", exc)
        return f"[Grok] Error: {str(exc)[:120]}"
