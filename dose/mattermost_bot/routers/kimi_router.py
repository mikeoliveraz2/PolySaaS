"""
Kimi router — Moonshot Kimi API.
Sync — called from a threading.Thread in bot.py.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

KIMI_API_URL = "https://api.moonshot.cn/v1/chat/completions"
KIMI_MODEL = "moonshot-v1-8k"


def handle(message: str, user_id: str, channel_id: str) -> str:
    api_key = getattr(settings, 'KIMI_API_KEY', '')
    if not api_key:
        return "⚠️ Kimi is offline — KIMI_API_KEY not configured."

    clean = message.replace('@kimi', '').replace('@Kimi', '').strip()
    if not clean:
        return "Hi! Ask me anything by tagging **@kimi** followed by your question."

    try:
        resp = requests.post(
            KIMI_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": KIMI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Kimi, an AI assistant by Moonshot AI. "
                            "You are integrated into PolySaaS as an AI Peer in a Mattermost team channel. "
                            "Be helpful, multilingual-friendly, and concise. Use markdown where appropriate."
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
        logger.warning("[Kimi] API timeout")
        return "⚠️ Kimi is thinking... (timeout — try again)"
    except Exception as exc:
        logger.error("[Kimi] API error: %s", exc)
        return f"⚠️ Kimi hit an error: {str(exc)[:120]}"
