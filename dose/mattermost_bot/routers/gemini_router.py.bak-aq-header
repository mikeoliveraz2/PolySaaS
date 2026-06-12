"""
Gemini router -- calls Google Gemini API and returns the response text.
Sync (no asyncio) -- called from a threading.Thread in bot.py.
"""
import logging
import re
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

_MENTION_RE = re.compile(r'@(?:gemini|gem|anyone)\b', re.IGNORECASE)

SYSTEM_PROMPT = (
    "You are Gemini, a synthesis-focused AI peer powered by Google, integrated into "
    "the PolySaaS Mattermost workspace. PolySaaS is a multi-tenant SaaS "
    "orchestration platform (Django/DOSE) that bundles open-source apps. "
    "You collaborate with humans (MO = Mike Oliver, founder; Shela = co-developer) "
    "and other AI peers (@grok, @copilot, @github, @cc, @wsc, @kimi, @windsurf). "
    "You excel at multi-step reasoning, creative thinking, and broad knowledge synthesis. "
    "Be concise and helpful. Use markdown where appropriate. "
    "Keep responses under 150 words unless asked for detail."
)


def handle(message: str, user_id: str, channel_id: str) -> str:
    """Call Google Gemini API. Returns response text or an error string."""
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return "[Gemini] Offline -- GEMINI_API_KEY not configured."

    clean = _MENTION_RE.sub('', message).strip()
    if not clean:
        return (
            "Hi! I'm **Gemini**, your Google AI peer on PolySaaS. "
            "Tag **@gemini** (or **@gem**) with a question."
        )

    try:
        resp = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": clean}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1500},
            },
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.Timeout:
        logger.warning("[Gemini] API timeout")
        return "[Gemini] Busy... (timeout -- try again)"
    except Exception as exc:
        logger.error("[Gemini] API error: %s", exc)
        return f"[Gemini] Error: {str(exc)[:120]}"
