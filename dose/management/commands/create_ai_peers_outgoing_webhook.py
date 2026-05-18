"""
Management command: create the Mattermost outgoing webhook for AI peers.

Creates or reuses an outgoing webhook for a Mattermost team and points it at
PolySaaS' AI peers callback endpoint.

Usage:
    python manage.py create_ai_peers_outgoing_webhook --team polysaast
    python manage.py create_ai_peers_outgoing_webhook --team polysaast --channel-name town-square
    python manage.py create_ai_peers_outgoing_webhook --team polysaast --callback-url https://polysaas.example
"""
from __future__ import annotations

import os
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.management.base import BaseCommand


DEFAULT_TRIGGER_WORDS = [
    'supergrok',
    'gemini',
    'windsurf',
    'gem',
    'ws',
    'grok',
]


class Command(BaseCommand):
    help = 'Create or reuse the Mattermost outgoing webhook used by AI peers'

    def add_arguments(self, parser):
        parser.add_argument('--team', required=True, help='Mattermost team name that owns the webhook')
        parser.add_argument(
            '--channel-name',
            default='town-square',
            help='Optional Mattermost channel name to bind the webhook to (default: town-square)',
        )
        parser.add_argument(
            '--callback-url',
            default='',
            help='Public base URL for PolySaaS; defaults to AIASPEERS_BASE_URL or POLYSAAS_CORE_BASE_URL',
        )
        parser.add_argument(
            '--display-name',
            default='PolySaaS AI Peers',
            help='Outgoing webhook display name',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without calling Mattermost',
        )

    def handle(self, *args, **options):
        mm_url = getattr(settings, 'MATTERMOST_URL', '').rstrip('/')
        admin_token = getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '')
        if not mm_url or not admin_token:
            self.stderr.write(self.style.ERROR('MATTERMOST_URL and MATTERMOST_ADMIN_TOKEN must be set'))
            return

        team_input = options['team'].strip()
        channel_name = options['channel_name'].strip()
        callback_base = self._resolve_callback_base(options['callback_url'])
        if not callback_base:
            self.stderr.write(self.style.ERROR(
                'No callback base URL found. Pass --callback-url or set AIASPEERS_BASE_URL / POLYSAAS_CORE_BASE_URL.'
            ))
            return

        callback_url = urljoin(callback_base.rstrip('/') + '/', 'dose/webhook/ai-peers/')
        headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}

        team = self._resolve_team(mm_url, headers, team_input)
        team_id = team.get('id', '')
        team_name = team.get('name', '')
        if not team_id:
            self.stderr.write(self.style.ERROR(
                f"Team '{team_input}' was not found. Pass the team handle (for example: polysaas-online-llc) or display name."
            ))
            return

        self.stdout.write(
            f"Resolved team '{team_input}' -> name='{team_name}' display='{team.get('display_name', '')}' id={team_id}"
        )

        channel_id = ''
        if channel_name:
            channel_id = self._get_channel_id(mm_url, headers, team_id, channel_name)
            if channel_id:
                self.stdout.write(f"Resolved channel '{channel_name}' to id={channel_id}")
            else:
                self.stdout.write(self.style.WARNING(
                    f"Channel '{channel_name}' was not found; webhook will still be team-scoped."
                ))

        hook_payload = {
            'team_id': team_id,
            'display_name': options['display_name'],
            'description': 'PolySaaS AI peers outgoing webhook for Town Square and @mentions',
            'trigger_words': DEFAULT_TRIGGER_WORDS,
            'callback_urls': [callback_url],
            'content_type': 'application/json',
        }
        if channel_id:
            hook_payload['channel_id'] = channel_id

        self.stdout.write(f"Webhook callback: {callback_url}")
        self.stdout.write(f"Trigger words: {', '.join(DEFAULT_TRIGGER_WORDS)}")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('[DRY RUN] Would create/reuse outgoing webhook with payload:'))
            self.stdout.write(str(hook_payload))
            return

        existing = self._find_existing_hook(mm_url, headers, team_id, hook_payload['display_name'], callback_url)
        if existing:
            self.stdout.write(self.style.SUCCESS(
                f"Outgoing webhook already exists (id={existing.get('id')}, token={existing.get('token', '')[:8]}...)"
            ))
            return

        resp = requests.post(
            f'{mm_url}/api/v4/hooks/outgoing',
            headers=headers,
            json=hook_payload,
            timeout=30,
        )
        if resp.status_code in (200, 201):
            hook = resp.json()
            self.stdout.write(self.style.SUCCESS(
                f"Created outgoing webhook id={hook.get('id')} token={hook.get('token', '')[:8]}..."
            ))
            self.stdout.write('Copy the token into AI_PEERS_WEBHOOK_TOKEN in your environment.')
            return

        self.stderr.write(self.style.ERROR(f'Webhook create failed ({resp.status_code}): {resp.text[:400]}'))

    def _resolve_callback_base(self, explicit: str) -> str:
        if explicit.strip():
            return explicit.strip().rstrip('/')
        env_candidates = [
            os.environ.get('AIASPEERS_BASE_URL', ''),
            os.environ.get('POLYSAAS_CORE_BASE_URL', ''),
            os.environ.get('APPSASPEERS_BASE_URL', ''),
        ]
        for candidate in env_candidates:
            if candidate and candidate.strip():
                return candidate.strip().rstrip('/')
        return ''

    def _resolve_team(self, mm_url: str, headers: dict, team_input: str) -> dict:
        # Fast path: treat input as canonical team handle.
        resp = requests.get(f'{mm_url}/api/v4/teams/name/{team_input}', headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json()

        # Fallback: search by display name / term and accept exact display_name or name matches.
        search = requests.post(
            f'{mm_url}/api/v4/teams/search',
            headers=headers,
            json={'term': team_input},
            timeout=15,
        )
        if search.status_code != 200:
            return {}

        for team in search.json() or []:
            if (team.get('display_name') or '').lower() == team_input.lower():
                return team
        for team in search.json() or []:
            if (team.get('name') or '').lower() == team_input.lower():
                return team
        if search.json():
            return search.json()[0]
        return {}

    def _get_channel_id(self, mm_url: str, headers: dict, team_id: str, channel_name: str) -> str:
        resp = requests.get(
            f'{mm_url}/api/v4/teams/{team_id}/channels/name/{channel_name}',
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get('id', '')
        return ''

    def _find_existing_hook(self, mm_url: str, headers: dict, team_id: str, display_name: str, callback_url: str):
        resp = requests.get(
            f'{mm_url}/api/v4/hooks/outgoing',
            headers=headers,
            params={'team_id': team_id},
            timeout=30,
        )
        if resp.status_code != 200:
            return None

        payload = resp.json()
        if isinstance(payload, dict):
            hooks = payload.get('outgoing_webhooks') or payload.get('hooks') or []
        else:
            hooks = payload

        for hook in hooks:
            if hook.get('team_id') != team_id:
                continue
            if hook.get('display_name') != display_name:
                continue
            callback_urls = hook.get('callback_urls') or []
            if callback_url in callback_urls:
                return hook
        return None
