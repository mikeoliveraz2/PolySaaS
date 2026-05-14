"""
Gemini router — calls Google Gemini API and returns the response text.
Sync (no asyncio) — called from a threading.Thread in bot.py.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_DISPLAY_NAME = "Gemini"
GEMINI_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Google_Gemini_logo.svg/120px-Google_Gemini_logo.svg.png"


def handle(message: str, user_id: str, channel_id: str) -> str:
    """Call Google Gemini API. Returns response text or an error string."""
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return "⚠️ Gemini is offline — GEMINI_API_KEY not configured."

    clean = message.replace('@gemini', '').replace('@Gemini', '').strip()
    if not clean:
        return "Hi! Ask me anything by tagging **@gemini** followed by your question."

    try:
        resp = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": (
                                    "You are Gemini, an AI assistant by Google. "
                                    "You are participating in a Mattermost team channel. "
                                    "Be helpful, direct, and concise. "
                                    f"User message: {clean}"
                                )
                            }
                        ]
                    }
                ],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1500},
            },
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.Timeout:
        logger.warning("[Gemini] API timeout")
        return "⚠️ Gemini is busy... (timeout — try again)"
    except Exception as exc:
        logger.error("[Gemini] API error: %s", exc)
        return f"⚠️ Gemini hit an error: {str(exc)[:120]}"
