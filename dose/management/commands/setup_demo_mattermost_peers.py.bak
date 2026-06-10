"""
Provision demo AI peers in Mattermost Town Square.

Creates @github, @copilot, @grok, @gemini bot accounts, adds them to the tenant's
Town Square channel, posts welcome intros, and prints env vars for .env.

Usage:
    python manage.py setup_demo_mattermost_peers --tenant-schema=polysaast122
    python manage.py setup_demo_mattermost_peers --team=polysaas-test-122
    python manage.py setup_demo_mattermost_peers --tenant-schema=polysaast122 --dry-run
"""
import json
import secrets

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


DEMO_BOTS = [
    {
        'username': 'github',
        'display_name': 'GitHub',
        'description': 'PolySaaS repo peer — PRs, issues, and project context for mikeoliveraz2/PolySaaS.',
        'env_key': 'BOT_TOKEN_GITHUB',
        'intro': (
            "👋 I'm **@github**, your repo peer for **mikeoliveraz2/PolySaaS**. "
            "Ask about branches, PRs, or what's in the codebase."
        ),
    },
    {
        'username': 'copilot',
        'display_name': 'Copilot',
        'description': 'Engineering peer — implementation planning and next steps for PolySaaS.',
        'env_key': 'BOT_TOKEN_COPILOT',
        'intro': (
            "👋 I'm **@copilot**, your engineering peer. "
            "Tag me for implementation plans, code structure, and next steps."
        ),
    },
    {
        'username': 'grok',
        'display_name': 'Grok',
        'description': 'xAI Grok peer — fast synthesis and direct analysis.',
        'env_key': 'BOT_TOKEN_GROK',
        'fallback_env_key': 'BOT_TOKEN_SUPERGROK',
        'intro': (
            "👋 I'm **@grok** (xAI). Tag me for fast, direct answers and tradeoff analysis."
        ),
    },
    {
        'username': 'gemini',
        'display_name': 'Gemini',
        'description': 'Google Gemini peer — synthesis and multi-step reasoning.',
        'env_key': 'BOT_TOKEN_GEMINI',
        'fallback_env_key': 'BOT_TOKEN_GEM',
        'intro': (
            "👋 I'm **@gemini** (Google). Tag me for synthesis, reasoning, and review."
        ),
    },
]


class Command(BaseCommand):
    help = 'Create demo Mattermost AI peers (github, copilot, grok, gemini) in Town Square'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-schema', type=str, help='Tenant schema (e.g. polysaast122)')
        parser.add_argument('--team', type=str, help='Mattermost team handle (overrides tenant lookup)')
        parser.add_argument('--channel', type=str, default='town-square', help='Channel name (default: town-square)')
        parser.add_argument('--dry-run', action='store_true', help='Show plan without API calls')
        parser.add_argument('--no-welcome', action='store_true', help='Skip welcome posts')

    def handle(self, *args, **options):
        mm_url = getattr(settings, 'MATTERMOST_URL', '').rstrip('/')
        admin_token = getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '')

        if not mm_url:
            self.stderr.write(self.style.ERROR('MATTERMOST_URL is not configured'))
            return
        if not admin_token and not options['dry_run']:
            self.stderr.write(self.style.ERROR('MATTERMOST_ADMIN_TOKEN is required'))
            return

        team_name = options.get('team') or self._team_from_tenant(options.get('tenant_schema'))
        if not team_name:
            self.stderr.write(self.style.ERROR(
                'Pass --team=<mattermost-team> or --tenant-schema=<schema> with mm_team_name in TenantApp'
            ))
            return

        self.stdout.write(f"Mattermost: {mm_url}")
        self.stdout.write(f"Team: {team_name}")
        self.stdout.write(f"Channel: {options['channel']}")
        self.stdout.write(f"Demo peers: {', '.join('@' + b['username'] for b in DEMO_BOTS)}")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('[DRY RUN] No changes made.'))
            return

        headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}
        team_id, channel_id = self._resolve_team_channel(mm_url, headers, team_name, options['channel'])
        if not team_id:
            self.stderr.write(self.style.ERROR(f"Team '{team_name}' not found"))
            return
        if not channel_id:
            self.stderr.write(self.style.ERROR(f"Channel '{options['channel']}' not found on team '{team_name}'"))
            return

        tokens = {}
        for bot in DEMO_BOTS:
            self.stdout.write(f"\n--- @{bot['username']} ---")
            user_id, token = self._ensure_bot(mm_url, headers, bot)
            if not user_id or not token:
                self.stderr.write(self.style.ERROR(f"  Failed @{bot['username']}"))
                continue
            tokens[bot['username']] = token
            self._add_to_team(mm_url, headers, team_id, user_id, bot['username'])
            self._add_to_channel(mm_url, headers, channel_id, user_id, bot['username'])
            self.stdout.write(self.style.SUCCESS(f"  Ready — {bot['env_key']}={token[:10]}..."))

        if options.get('tenant_schema') and tokens:
            self._store_tenant_tokens(options['tenant_schema'], tokens)

        if not options['no_welcome']:
            self._post_welcomes(mm_url, tokens, channel_id)

        self.stdout.write(self.style.SUCCESS('\n=== Demo peers ready in Town Square ==='))
        self.stdout.write('\nAdd to .env (or Secret Manager):')
        for bot in DEMO_BOTS:
            tok = tokens.get(bot['username'])
            if tok:
                self.stdout.write(f"  {bot['env_key']}={tok}")
                fb = bot.get('fallback_env_key')
                if fb:
                    self.stdout.write(f"  {fb}={tok}")
        self.stdout.write(
            '\nNext:\n'
            '  1. Restart Django after updating .env\n'
            '  2. python manage.py run_mattermost_bot   (or configure outgoing webhook)\n'
            '  3. In Town Square: @github @copilot @grok @gemini — or say hello everyone\n'
        )

    def _team_from_tenant(self, schema):
        if not schema:
            return None
        with connection.cursor() as cur:
            cur.execute(f"SET search_path TO {schema}, public")
        from dose.models import TenantApp
        ta = (
            TenantApp.objects.filter(app_name__iexact='mattermost')
            .exclude(extra_config__isnull=True)
            .order_by('-id')
            .first()
        )
        if not ta or not ta.extra_config:
            return None
        return ta.extra_config.get('mm_team_name') or ta.extra_config.get('mm_team')

    def _resolve_team_channel(self, mm_url, headers, team_name, channel_name):
        team_id = channel_id = None
        resp = requests.get(f'{mm_url}/api/v4/teams/name/{team_name}', headers=headers, timeout=20)
        if resp.status_code == 200:
            team_id = resp.json().get('id')
        if team_id:
            ch = requests.get(
                f'{mm_url}/api/v4/teams/{team_id}/channels/name/{channel_name}',
                headers=headers,
                timeout=20,
            )
            if ch.status_code == 200:
                channel_id = ch.json().get('id')
        return team_id, channel_id

    def _ensure_bot(self, mm_url, headers, bot):
        username = bot['username']
        resp = requests.get(f'{mm_url}/api/v4/users/username/{username}', headers=headers, timeout=20)
        if resp.status_code == 200:
            user_id = resp.json()['id']
            self.stdout.write(f"  @{username} exists (id={user_id})")
        else:
            resp = requests.post(
                f'{mm_url}/api/v4/bots',
                headers=headers,
                json={
                    'username': username,
                    'display_name': bot['display_name'],
                    'description': bot['description'],
                },
                timeout=20,
            )
            if resp.status_code not in (200, 201):
                self.stderr.write(f"  Create failed: {resp.text[:200]}")
                return None, None
            user_id = resp.json().get('user_id')
            self.stdout.write(f"  Created @{username}")

        tok_resp = requests.post(
            f'{mm_url}/api/v4/users/{user_id}/tokens',
            headers=headers,
            json={'description': f'PolySaaS demo peer @{username}'},
            timeout=20,
        )
        if tok_resp.status_code not in (200, 201):
            self.stderr.write(f"  Token failed: {tok_resp.text[:200]}")
            return user_id, None
        return user_id, tok_resp.json().get('token')

    def _add_to_team(self, mm_url, headers, team_id, user_id, username):
        resp = requests.post(
            f'{mm_url}/api/v4/teams/{team_id}/members',
            headers=headers,
            json={'team_id': team_id, 'user_id': user_id},
            timeout=20,
        )
        if resp.status_code in (200, 201):
            self.stdout.write(f"  Added @{username} to team")
        elif 'already' in (resp.text or '').lower():
            pass

    def _add_to_channel(self, mm_url, headers, channel_id, user_id, username):
        resp = requests.post(
            f'{mm_url}/api/v4/channels/{channel_id}/members',
            headers=headers,
            json={'user_id': user_id},
            timeout=20,
        )
        if resp.status_code in (200, 201):
            self.stdout.write(f"  Added @{username} to Town Square")

    def _post_welcomes(self, mm_url, tokens, channel_id):
        for bot in DEMO_BOTS:
            token = tokens.get(bot['username'])
            if not token:
                continue
            try:
                requests.post(
                    f'{mm_url}/api/v4/posts',
                    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                    json={'channel_id': channel_id, 'message': bot['intro']},
                    timeout=20,
                )
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"  Welcome post failed for @{bot['username']}: {exc}"))

    def _store_tenant_tokens(self, schema, tokens):
        with connection.cursor() as cur:
            cur.execute(f"SET search_path TO {schema}, public")
        from dose.models import TenantApp
        ta = TenantApp.objects.filter(app_name__iexact='mattermost').order_by('-id').first()
        if not ta:
            return
        cfg = dict(ta.extra_config or {})
        cfg['demo_peer_tokens'] = tokens
        cfg['demo_peers_setup'] = True
        ta.extra_config = cfg
        ta.save(update_fields=['extra_config'])
        self.stdout.write(self.style.SUCCESS(f"  Stored demo_peer_tokens on TenantApp id={ta.id} ({schema})"))
