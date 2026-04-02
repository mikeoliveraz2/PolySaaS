"""
AI as Peers — Multi-LLM router for Mattermost channels.

When a user @mentions an AI peer (@CC, @SuperGrok, etc.) in a Mattermost
channel, this service:
  1. Identifies which peer was mentioned
  2. Gathers recent channel context (last N messages)
  3. Calls the appropriate LLM API (Anthropic for CC, xAI for SuperGrok)
  4. Posts the response back to the channel AS that bot user

Each bot has its own Mattermost bot account with a personal access token,
so replies appear under the correct identity.
"""
import logging
import json
import requests
from typing import Optional, Dict, Any, List

from django.conf import settings

logger = logging.getLogger(__name__)

PEER_REGISTRY: Dict[str, Dict[str, Any]] = {}


def _mm_url():
    return getattr(settings, 'MATTERMOST_URL', 'https://mm.polysaas.online').rstrip('/')


def _mm_headers(token: str) -> dict:
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


def register_peer(username: str, display_name: str, provider: str,
                  bot_token: str, system_prompt: str = ''):
    """Register an AI peer in the in-memory registry."""
    PEER_REGISTRY[username.lower()] = {
        'username': username,
        'display_name': display_name,
        'provider': provider,       # 'anthropic' | 'xai'
        'bot_token': bot_token,
        'system_prompt': system_prompt,
    }
    logger.info("Registered AI peer: @%s (%s via %s)", username, display_name, provider)


def get_channel_context(channel_id: str, limit: int = 15) -> List[dict]:
    """Fetch the last N messages from a Mattermost channel for conversation context."""
    admin_token = getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '')
    if not admin_token:
        return []
    url = f"{_mm_url()}/api/v4/channels/{channel_id}/posts"
    try:
        resp = requests.get(url, headers=_mm_headers(admin_token),
                            params={'per_page': limit}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        posts = data.get('posts', {})
        order = data.get('order', [])
        messages = []
        for post_id in reversed(order):
            p = posts[post_id]
            messages.append({
                'role': 'user',
                'username': p.get('props', {}).get('override_username', '') or p.get('user_id', ''),
                'content': p.get('message', ''),
            })
        return messages
    except Exception as e:
        logger.warning("Failed to fetch channel context: %s", e)
        return []


def _call_anthropic(messages: list, system_prompt: str) -> str:
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        return "[CC] Anthropic API key not configured."
    conversation = []
    for m in messages:
        role = 'assistant' if m.get('is_bot') else 'user'
        prefix = f"@{m['username']}: " if m.get('username') else ''
        conversation.append({'role': role, 'content': f"{prefix}{m['content']}"})

    try:
        resp = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': 'claude-sonnet-4-6',
                'max_tokens': 1024,
                'system': system_prompt or (
                    "You are CC (Claude), an AI peer collaborating in a Mattermost channel "
                    "with humans and other AI agents on the PolySaaS platform. Be concise, "
                    "helpful, and collaborative. You can @mention other peers to loop them in."
                ),
                'messages': conversation,
            },
            timeout=60,
        )
        print(f"[DEBUG] Anthropic response status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"[DEBUG] Anthropic error body: {resp.text}")
        
        resp.raise_for_status()
        data = resp.json()
        return data['content'][0]['text']
    except Exception as e:
        print(f"[DEBUG] Anthropic error: {e}")
        logger.error("Anthropic API error: %s", e)
        return f"[CC] Error calling Anthropic: {e}"


def _call_xai(messages: list, system_prompt: str) -> str:
    api_key = getattr(settings, 'XAI_API_KEY', '')
    if not api_key:
        return "[SuperGrok] xAI API key not configured."
    conversation = []
    for m in messages:
        role = 'assistant' if m.get('is_bot') else 'user'
        prefix = f"@{m['username']}: " if m.get('username') else ''
        conversation.append({'role': role, 'content': f"{prefix}{m['content']}"})

    try:
        resp = requests.post(
            'https://api.x.ai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'grok-3',
                'messages': [
                    {'role': 'system', 'content': system_prompt or (
                        "You are SuperGrok, an AI peer collaborating in a Mattermost channel "
                        "with humans and other AI agents on the PolySaaS platform. Be concise, "
                        "direct, and collaborative. You can @mention other peers to loop them in."
                    )},
                    *conversation,
                ],
                'max_tokens': 1024,
            },
            timeout=60,
        )
        print(f"[DEBUG] xAI response status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"[DEBUG] xAI error body: {resp.text}")
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        print(f"[DEBUG] xAI error: {e}")
        logger.error("xAI API error: %s", e)
        return f"[SuperGrok] Error calling xAI: {e}"


def _call_gemini(messages: list, system_prompt: str) -> str:
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return "[CC] Gemini API key not configured."
    conversation = []
    for m in messages:
        role = 'model' if m.get('is_bot') else 'user'
        prefix = f"@{m['username']}: " if m.get('username') else ''
        conversation.append({'role': role, 'parts': [{'text': f"{prefix}{m['content']}"}]})

    try:
        print(f"[DEBUG] Gemini request to: https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key[:5]}...")
        resp = requests.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}',
            headers={'Content-Type': 'application/json'},
            json={
                'system_instruction': {'parts': [{'text': system_prompt or (
                    "You are CC, an AI peer collaborating in a Mattermost channel "
                    "with humans and other AI agents on the PolySaaS platform. Be concise, "
                    "helpful, and collaborative. You can @mention other peers to loop them in."
                )}]},
                'contents': conversation,
                'generationConfig': {'maxOutputTokens': 1024},
            },
            timeout=60,
        )
        print(f"[DEBUG] Gemini response status: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"[DEBUG] Gemini error: {e}")
        logger.error("Gemini API error: %s", e)
        return f"[CC] Error calling Gemini: {e}"


LLM_PROVIDERS = {
    'anthropic': _call_anthropic,
    'xai': _call_xai,
    'gemini': _call_gemini,
}


def handle_mention(peer_username: str, channel_id: str,
                   trigger_message: str, trigger_user: str,
                   post_id: str = '') -> Optional[str]:
    """
    Main entry point. Called when someone @mentions an AI peer.
    Returns the response text (also posts it to the channel).
    """
    print(f"[DEBUG] handle_mention: peer={peer_username}, channel={channel_id}")
    peer = PEER_REGISTRY.get(peer_username.lower())
    if not peer:
        logger.warning("Unknown AI peer mentioned: @%s", peer_username)
        return None

    context = get_channel_context(channel_id)

    if not context:
        print(f"[DEBUG] No context found for channel {channel_id}, using trigger message")
        context = [{'role': 'user', 'username': trigger_user, 'content': trigger_message}]

    provider_fn = LLM_PROVIDERS.get(peer['provider'])
    if not provider_fn:
        logger.error("No LLM provider '%s' for peer @%s", peer['provider'], peer_username)
        return None

    print(f"[DEBUG] Calling provider {peer['provider']} for @{peer_username}")
    response_text = provider_fn(context, peer.get('system_prompt', ''))
    print(f"[DEBUG] AI Response: {response_text[:100]}...")

    _post_as_bot(peer['bot_token'], channel_id, response_text)

    return response_text


def _post_as_bot(bot_token: str, channel_id: str, message: str, root_id: str = ''):
    """Post a message to a Mattermost channel as a specific bot user."""
    print(f"[DEBUG] _post_as_bot: channel={channel_id}, token={bot_token[:5]}..., root_id={root_id}")
    payload = {
        'channel_id': channel_id,
        'message': message,
    }
    if root_id:
        payload['root_id'] = root_id

    try:
        resp = requests.post(
            f"{_mm_url()}/api/v4/posts",
            headers=_mm_headers(bot_token),
            json=payload,
            timeout=15,
        )
        if resp.status_code == 400 and root_id:
            print(f"[DEBUG] Mattermost root_id failed, retrying without threading...")
            payload.pop('root_id')
            resp = requests.post(
                f"{_mm_url()}/api/v4/posts",
                headers=_mm_headers(bot_token),
                json=payload,
                timeout=15,
            )

        if resp.status_code != 201:
            print(f"[DEBUG] Mattermost post error body: {resp.text}")
        resp.raise_for_status()
        logger.info("AI peer posted to channel %s", channel_id)
    except Exception as e:
        logger.error("Failed to post as bot to channel %s: %s", channel_id, e)
