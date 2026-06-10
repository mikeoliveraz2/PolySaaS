"""Town Square demo roster — Grok, Gemini, Copilot only (reduces channel load)."""

import logging

import requests

logger = logging.getLogger(__name__)

DEMO_TOWN_SQUARE_USERNAMES = ('grok', 'gemini', 'copilot')

# Bot accounts removed from Town Square during demo sync (may still exist on the server).
PRUNE_FROM_TOWN_SQUARE_USERNAMES = (
    'github',
    'cc',
    'cursor',
    'windsurf',
    'wsc',
    'ws',
    'kimi',
    'router',
    'openclaw',
    'supergrok',
    'code-reviewer',
    'dev-helper',
    'polysaas-guide',
)


def sync_town_square_demo_roster(mm_url, headers, team_id, log=None):
    """Ensure demo peers are in town-square; remove extra bot channel members."""
    mm_url = (mm_url or '').rstrip('/')
    if not mm_url or not team_id:
        return

    def _write(msg):
        if log:
            log(msg)
        else:
            logger.info(msg)

    ch_resp = requests.get(
        f'{mm_url}/api/v4/teams/{team_id}/channels/name/town-square',
        headers=headers,
        timeout=20,
    )
    if ch_resp.status_code != 200:
        _write(f'town-square not found on team {team_id}: HTTP {ch_resp.status_code}')
        return
    channel_id = ch_resp.json().get('id')
    if not channel_id:
        return

    def _user_id(username):
        r = requests.get(
            f'{mm_url}/api/v4/users/username/{username}',
            headers=headers,
            timeout=10,
        )
        if r.status_code != 200:
            return None
        return r.json().get('id')

    for username in DEMO_TOWN_SQUARE_USERNAMES:
        uid = _user_id(username)
        if not uid:
            continue
        r = requests.post(
            f'{mm_url}/api/v4/channels/{channel_id}/members',
            headers=headers,
            json={'user_id': uid},
            timeout=10,
        )
        if r.status_code in (200, 201):
            _write(f'  + @{username} in town-square')
        elif 'already' in (r.text or '').lower():
            pass

    for username in PRUNE_FROM_TOWN_SQUARE_USERNAMES:
        uid = _user_id(username)
        if not uid:
            continue
        r = requests.delete(
            f'{mm_url}/api/v4/channels/{channel_id}/members/{uid}',
            headers=headers,
            timeout=10,
        )
        if r.status_code == 200:
            _write(f'  - @{username} removed from town-square')
