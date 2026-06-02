"""
Grok router — calls xAI API and returns the response text.
Sync (no asyncio) — called from a threading.Thread in bot.py.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GROK_API_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-3"
GROK_DISPLAY_NAME = "Grok"
GROK_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/XAI_Logo.svg/120px-XAI_Logo.svg.png"


def handle(message: str, user_id: str, channel_id: str) -> str:
    """Call xAI Grok API. Returns response text or an error string."""
    api_key = getattr(settings, 'XAI_API_KEY', '')
    if not api_key:
        return "⚠️ Grok is offline — XAI_API_KEY not configured."

    clean = message.replace('@grok', '').replace('@Grok', '').strip()
    if not clean:
        return "Hi! Ask me anything by tagging **@grok** followed by your question."

    try:
        resp = requests.post(
            GROK_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": GROK_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Grok, a helpful and witty AI built by xAI. "
                            "You are integrated into PolySaaS as an AI Peer in a Mattermost team channel. "
                            "Be direct and concise. Use markdown formatting where appropriate."
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
        logger.warning("[Grok] API timeout")
        return "⚠️ Grok is thinking hard... (timeout — try again)"
    except Exception as exc:
        logger.error("[Grok] API error: %s", exc)
        return f"⚠️ Grok hit an error: {str(exc)[:120]}"
