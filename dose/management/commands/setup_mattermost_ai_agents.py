"""
Management command: setup_mattermost_ai_agents

Creates Mattermost bot accounts for AI agents and configures them.
This should be run after Mattermost is provisioned for a tenant.

Creates 4 bots:
1. @windsurf - Code assistant with file access
2. @code-reviewer - Code evaluator
3. @dev-helper - General development help
4. @polysaas-guide - Platform expert

Usage:
    python manage.py setup_mattermost_ai_agents --tenant-schema=tenant_xyz
    python manage.py setup_mattermost_ai_agents --all-tenants
    python manage.py setup_mattermost_ai_agents --dry-run
"""
import os
import json
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = 'Create Mattermost bot accounts for AI agents'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-schema', type=str, help='Specific tenant schema to setup')
        parser.add_argument('--all-tenants', action='store_true', help='Setup for all tenants')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        tenant_schema = options.get('tenant_schema')
        all_tenants = options.get('all_tenants')

        # Mattermost admin credentials
        mm_url = getattr(settings, 'MATTERMOST_URL', 'https://polysaas-mattermost.onrender.com')
        mm_admin_token = os.getenv('MATTERMOST_ADMIN_TOKEN', '')
        
        if not mm_admin_token and not dry_run:
            self.stdout.write(self.style.ERROR('MATTERMOST_ADMIN_TOKEN environment variable required'))
            return

        # Bot configurations
        BOTS = [
            {
                'username': 'windsurf',
                'password': self._generate_password(),
                'display_name': 'Windsurf',
                'description': 'AI code assistant with direct codebase access. Ask me to show any source file!',
            },
            {
                'username': 'code-reviewer',
                'password': self._generate_password(),
                'display_name': 'Code Reviewer',
                'description': 'Senior code reviewer. I analyze code for security, performance, and best practices.',
            },
            {
                'username': 'dev-helper',
                'password': self._generate_password(),
                'display_name': 'Dev Helper',
                'description': 'Friendly development assistant. Ask me anything about programming!',
            },
            {
                'username': 'polysaas-guide',
                'password': self._generate_password(),
                'display_name': 'PolySaaS Guide',
                'description': 'Platform expert. I know all about PolySaaS architecture and features.',
            },
        ]

        self.stdout.write(f'Setting up AI agents in Mattermost at {mm_url}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN] Would create the following bots:'))
            for bot in BOTS:
                self.stdout.write(f"  - @{bot['username']} ({bot['display_name']})")
            return

        # Get or create bots
        created_tokens = {}
        for bot in BOTS:
            token = self._create_or_get_bot(mm_url, mm_admin_token, bot)
            if token:
                created_tokens[bot['username']] = token
                self.stdout.write(self.style.SUCCESS(f"Created bot @{bot['username']} with token"))
                
                # Store token in environment or settings
                # In production, these should go to a secure vault
                self._store_bot_token(bot['username'], token)
            else:
                self.stdout.write(self.style.ERROR(f"Failed to create bot @{bot['username']}"))

        # Invite bots to Town Square
        team_name = 'polysaas-dev-team'
        town_square_id = self._get_town_square_id(mm_url, mm_admin_token, team_name)
        
        if town_square_id:
            for username in created_tokens:
                self._add_bot_to_channel(mm_url, mm_admin_token, username, town_square_id)
            
            self.stdout.write(self.style.SUCCESS(f'All bots added to Town Square'))
            
            # Have bots introduce themselves
            self._bots_say_hello(mm_url, created_tokens, town_square_id)
        
        self.stdout.write(self.style.SUCCESS('\nAI agents are ready!'))
        self.stdout.write('Bots will respond to:')
        self.stdout.write('  - "hello everyone" - All bots greet')
        self.stdout.write('  - @windsurf show me filename.py - Shows source code')
        self.stdout.write('  - @code-reviewer evaluate this - Reviews recent code')
        self.stdout.write('  - @dev-helper <question> - General help')
        self.stdout.write('  - @polysaas-guide <question> - Platform questions')

    def _generate_password(self):
        import secrets
        return secrets.token_urlsafe(16)

    def _create_or_get_bot(self, mm_url: str, admin_token: str, bot_config: dict) -> str:
        """Create bot account and return bot token."""
        headers = {'Authorization': f'Bearer {admin_token}'}
        
        try:
            # Check if bot already exists
            resp = requests.get(
                f'{mm_url}/api/v4/users/username/{bot_config["username"]}',
                headers=headers
            )
            
            if resp.status_code == 200:
                user_id = resp.json()['id']
                self.stdout.write(f"  Bot @{bot_config['username']} already exists")
            else:
                # Create bot
                resp = requests.post(
                    f'{mm_url}/api/v4/bots',
                    headers={**headers, 'Content-Type': 'application/json'},
                    json={
                        'username': bot_config['username'],
                        'display_name': bot_config['display_name'],
                        'description': bot_config['description'],
                    }
                )
                
                if resp.status_code not in [201, 200]:
                    self.stdout.write(self.style.WARNING(f"  Bot create failed: {resp.text}"))
                    # Try creating as regular user
                    resp = requests.post(
                        f'{mm_url}/api/v4/users',
                        headers={**headers, 'Content-Type': 'application/json'},
                        json={
                            'username': bot_config['username'],
                            'password': bot_config['password'],
                            'email': f"{bot_config['username']}@polysaas.local",
                            'first_name': bot_config['display_name'],
                        }
                    )
                    if resp.status_code not in [201, 200]:
                        return None
                    user_id = resp.json()['id']
                else:
                    user_id = resp.json()['user_id']
            
            # Create bot token
            resp = requests.post(
                f'{mm_url}/api/v4/users/{user_id}/tokens',
                headers={**headers, 'Content-Type': 'application/json'},
                json={'description': 'AI Agent Access Token'}
            )
            
            if resp.status_code in [201, 200]:
                return resp.json()['token']
            
            return None
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error creating bot: {e}"))
            return None

    def _store_bot_token(self, username: str, token: str):
        """Store bot token securely."""
        # In production, use a proper secret manager
        # For now, log to console for setup
        self.stdout.write(f"  Token for {username}: {token[:8]}... (store in env var {username.upper()}_BOT_TOKEN)")

    def _get_town_square_id(self, mm_url: str, admin_token: str, team_name: str) -> str:
        """Get Town Square channel ID."""
        headers = {'Authorization': f'Bearer {admin_token}'}
        
        try:
            # Get team
            resp = requests.get(
                f'{mm_url}/api/v4/teams/name/{team_name}',
                headers=headers
            )
            if resp.status_code != 200:
                return None
            
            team_id = resp.json()['id']
            
            # Get channels
            resp = requests.get(
                f'{mm_url}/api/v4/teams/{team_id}/channels',
                headers=headers
            )
            if resp.status_code != 200:
                return None
            
            channels = resp.json()
            for ch in channels:
                if ch['name'] == 'town-square':
                    return ch['id']
            
            return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error getting Town Square: {e}"))
            return None

    def _add_bot_to_channel(self, mm_url: str, admin_token: str, username: str, channel_id: str):
        """Add bot user to channel."""
        headers = {'Authorization': f'Bearer {admin_token}'}
        
        try:
            # Get user ID
            resp = requests.get(
                f'{mm_url}/api/v4/users/username/{username}',
                headers=headers
            )
            if resp.status_code != 200:
                return
            
            user_id = resp.json()['id']
            
            # Add to channel
            resp = requests.post(
                f'{mm_url}/api/v4/channels/{channel_id}/members',
                headers={**headers, 'Content-Type': 'application/json'},
                json={'user_id': user_id}
            )
            
            if resp.status_code in [201, 200]:
                self.stdout.write(f"  Added @{username} to Town Square")
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Could not add @{username} to channel: {e}"))

    def _bots_say_hello(self, mm_url: str, tokens: dict, channel_id: str):
        """Have all bots introduce themselves."""
        introductions = [
            ('windsurf', "👋 Hello everyone! I'm **Windsurf**, your code assistant. I can show you any source file in the PolySaaS codebase. Just say `@windsurf show me filename.py`!"),
            ('code-reviewer', "👋 Hi! I'm the **Code Reviewer**. I analyze code for security, performance, and best practices. Share some code and ask me to review it!"),
            ('dev-helper', "👋 Hey there! I'm **Dev Helper** for all your programming questions. Stuck on something? I'm here to help!"),
            ('polysaas-guide', "👋 Greetings! I'm your **PolySaaS Guide**. Ask me anything about the platform architecture, passthrough services, or how things work!"),
        ]
        
        for username, message in introductions:
            token = tokens.get(username)
            if token:
                try:
                    requests.post(
                        f'{mm_url}/api/v4/posts',
                        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                        json={
                            'channel_id': channel_id,
                            'message': message,
                        }
                    )
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  Could not post intro for {username}: {e}"))
