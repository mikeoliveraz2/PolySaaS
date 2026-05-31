"""Copilot router — engineering-focused Anthropic peer for Mattermost."""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-6"


def handle(message: str, user_id: str, channel_id: str) -> str:
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        return "⚠️ Copilot is offline — ANTHROPIC_API_KEY not configured."

    clean = message
    for tag in ('@copilot', '@Copilot', '@anyone'):
        clean = clean.replace(tag, '')
    clean = clean.strip()
    if not clean:
        return (
            "Hi! I'm **Copilot**, your engineering peer on PolySaaS. "
            "Tag **@copilot** with an implementation question or next step."
        )

    repo = getattr(settings, 'GITHUB_REPO', 'mikeoliveraz2/PolySaaS')
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
                    "You are Copilot, an engineering-focused AI peer in a Mattermost channel "
                    f"for the PolySaaS project (GitHub: {repo}). Prioritize clear implementation "
                    "steps, code clarity, and actionable next steps. Be concise; use markdown."
                ),
                "messages": [{"role": "user", "content": clean}],
            },
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()['content'][0]['text']
    except requests.exceptions.Timeout:
        logger.warning("[Copilot] API timeout")
        return "⚠️ Copilot is thinking… (timeout — try again)"
    except Exception as exc:
        logger.error("[Copilot] API error: %s", exc)
        return f"⚠️ Copilot hit an error: {str(exc)[:120]}"
