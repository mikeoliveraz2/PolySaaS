"""
Management command: Create AI peer bot accounts in Mattermost.

Creates the current AI as Peers bot set for Mattermost, generates personal
access tokens for each, and registers them in the AI peer service.

Usage:
    python manage.py setup_ai_peers
    python manage.py setup_ai_peers --team olient
    python manage.py setup_ai_peers --dry-run
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from dose.services.ai_peer_service import register_peer

BOT_DEFINITIONS = [
    {
        'username': 'copilot',
        'display_name': 'Copilot',
        'description': 'AI peer for engineering execution and implementation planning in Mattermost channels.',
        'provider': 'anthropic',
    },
    {
        'username': 'cursor',
        'display_name': 'Cursor',
        'description': 'AI peer for repo-aware coding, debugging, and pragmatic iteration in Mattermost channels.',
        'provider': 'anthropic',
    },
    {
        'username': 'grok',
        'display_name': 'Grok',
        'description': 'AI peer powered by xAI Grok for direct analysis and fast synthesis in Mattermost channels.',
        'provider': 'xai',
    },
    {
        'username': 'gemini',
        'display_name': 'Gemini',
        'description': 'AI peer powered by Google Gemini for synthesis, reasoning, and collaborative review in Mattermost channels.',
        'provider': 'gemini',
    },
    {
        'username': 'windsurf',
        'display_name': 'Windsurf',
        'description': 'AI peer for software engineering, agentic coding workflows, and developer productivity in Mattermost channels.',
        'provider': 'windsurf',
    },
    {
        'username': 'router',
        'display_name': 'Router',
        'description': 'AI orchestration peer for routing work to the best human or AI collaborator in Mattermost channels.',
        'provider': 'anthropic',
    },
    {
        'username': 'openclaw',
        'display_name': 'OpenClaw',
        'description': 'AI peer for open systems, interoperability, and self-hosted workflow design in Mattermost channels.',
        'provider': 'anthropic',
    },
]


class Command(BaseCommand):
    help = 'Create AI peer bot accounts in Mattermost and register them in the peer service'

    def add_arguments(self, parser):
        parser.add_argument('--team', default='', help='Mattermost team name to add bots to')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    def handle(self, *args, **options):
        mm_url = getattr(settings, 'MATTERMOST_URL', '').rstrip('/')
        admin_token = getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '')

        if not mm_url or not admin_token:
            self.stderr.write(self.style.ERROR(
                'MATTERMOST_URL and MATTERMOST_ADMIN_TOKEN must be set in settings / .env'
            ))
            return

        headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}
        dry_run = options['dry_run']
        team_name = options.get('team', '')

        team_id = None
        if team_name:
            team_id = self._get_team_id(mm_url, headers, team_name)

        for bot_def in BOT_DEFINITIONS:
            self.stdout.write(f"\n--- Setting up @{bot_def['username']} ---")

            if dry_run:
                self.stdout.write(self.style.WARNING(f"  [DRY RUN] Would create bot @{bot_def['username']}"))
                continue

            bot_user_id, bot_token = self._ensure_bot(mm_url, headers, bot_def)
            if not bot_user_id or not bot_token:
                self.stderr.write(self.style.ERROR(f"  Failed to create bot @{bot_def['username']}"))
                continue

            register_peer(
                username=bot_def['username'],
                display_name=bot_def['display_name'],
                provider=bot_def['provider'],
                bot_token=bot_token,
            )

            if team_id:
                self._add_bot_to_team(mm_url, headers, bot_user_id, team_id, bot_def['username'])

            self.stdout.write(self.style.SUCCESS(
                f"  @{bot_def['username']} ready (provider={bot_def['provider']}, token={bot_token[:8]}...)"
            ))

        self.stdout.write(self.style.SUCCESS('\nAI peer setup complete.'))
        self.stdout.write(
            '\nNext steps:\n'
            '  1. Set the required provider API keys in your .env\n'
            '  2. Create an outgoing webhook in Mattermost pointing to:\n'
            f'     <your-polysaas-url>/dose/webhook/ai-peers/\n'
            '  3. Create trigger words for: #supergrok, #grok, #gemini, #windsurf, #gem, #ws\n'
            '  4. Copy the webhook token into AI_PEERS_WEBHOOK_TOKEN in .env\n'
        )

    def _ensure_bot(self, mm_url, headers, bot_def):
        """Create a bot if it doesn't exist, then ensure it has a token."""
        resp = requests.post(
            f'{mm_url}/api/v4/bots',
            headers=headers,
            json={
                'username': bot_def['username'],
                'display_name': bot_def['display_name'],
                'description': bot_def['description'],
            },
            timeout=15,
        )

        if resp.status_code == 201:
            bot = resp.json()
            bot_user_id = bot['user_id']
            self.stdout.write(f"  Created bot @{bot_def['username']} (user_id={bot_user_id})")
        elif resp.status_code == 400 and 'already exists' in resp.text.lower():
            self.stdout.write(f"  Bot @{bot_def['username']} already exists, fetching...")
            bot_user_id = self._get_existing_bot_user_id(mm_url, headers, bot_def['username'])
            if not bot_user_id:
                return None, None
        else:
            self.stderr.write(f"  Bot create failed ({resp.status_code}): {resp.text[:200]}")
            return None, None

        token = self._create_bot_token(mm_url, headers, bot_user_id, bot_def['username'])
        return bot_user_id, token

    def _get_existing_bot_user_id(self, mm_url, headers, username):
        resp = requests.get(f'{mm_url}/api/v4/bots', headers=headers,
                            params={'per_page': 200}, timeout=15)
        if resp.status_code == 200:
            for bot in resp.json():
                if bot.get('username') == username:
                    return bot['user_id']
        resp2 = requests.get(f'{mm_url}/api/v4/users/username/{username}',
                             headers=headers, timeout=15)
        if resp2.status_code == 200:
            return resp2.json().get('id')
        return None

    def _create_bot_token(self, mm_url, headers, bot_user_id, username):
        resp = requests.post(
            f'{mm_url}/api/v4/users/{bot_user_id}/tokens',
            headers=headers,
            json={'description': f'AI Peer token for @{username}'},
            timeout=15,
        )
        if resp.status_code == 200:
            token_data = resp.json()
            self.stdout.write(f"  Created access token for @{username}")
            return token_data['token']
        else:
            self.stderr.write(f"  Token create failed ({resp.status_code}): {resp.text[:200]}")
            return None

    def _get_team_id(self, mm_url, headers, team_name):
        resp = requests.get(f'{mm_url}/api/v4/teams/name/{team_name}',
                            headers=headers, timeout=15)
        if resp.status_code == 200:
            team_id = resp.json()['id']
            self.stdout.write(f"Found team '{team_name}' (id={team_id})")
            return team_id
        self.stderr.write(self.style.WARNING(f"Team '{team_name}' not found, skipping team assignment"))
        return None

    def _add_bot_to_team(self, mm_url, headers, bot_user_id, team_id, username):
        resp = requests.post(
            f'{mm_url}/api/v4/teams/{team_id}/members',
            headers=headers,
            json={'team_id': team_id, 'user_id': bot_user_id},
            timeout=15,
        )
        if resp.status_code in (200, 201):
            self.stdout.write(f"  Added @{username} to team")
        elif resp.status_code == 400 and 'already' in resp.text.lower():
            self.stdout.write(f"  @{username} already in team")
        else:
            self.stderr.write(f"  Team add failed ({resp.status_code}): {resp.text[:200]}")
