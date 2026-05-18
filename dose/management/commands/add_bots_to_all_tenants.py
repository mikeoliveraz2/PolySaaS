"""
Management command: Add all configured AI Peer bots to a tenant's Mattermost team.

Usage:
  python manage.py add_bots_to_all_tenants      # All tenants with MM configured
  python manage.py add_bots_to_all_tenants --tenant=t41  # Specific tenant
"""

import logging
from typing import Optional

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Add all configured AI Peer bots to a Mattermost team."

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            default=None,
            help='Specific tenant schema name (e.g., t41). Omit to process all.',
        )
        parser.add_argument(
            '--team-id',
            type=str,
            default=None,
            help='Specific MM team ID. Requires --mm-url as well.',
        )
        parser.add_argument(
            '--mm-url',
            type=str,
            default=None,
            help='Mattermost base URL. Required if --team-id is used.',
        )

    def handle(self, *args, **options):
        admin_token = getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '')
        if not admin_token:
            raise CommandError('MATTERMOST_ADMIN_TOKEN not configured in settings.')

        headers = {'Authorization': f'Bearer {admin_token}'}

        # Option 1: Direct MM credentials
        if options.get('team_id') and options.get('mm_url'):
            team_id = options['team_id']
            mm_url = options['mm_url']
            self._add_bots_to_team(mm_url, headers, team_id)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Bots added to team {team_id} at {mm_url}')
            )
            return

        # Option 2: All or specific tenant
        tenant_filter = options.get('tenant')
        from dose.models import TenantApp

        if tenant_filter:
            tenants = TenantApp.objects.filter(
                tenant__schema_name=tenant_filter,
                app__name__icontains='mattermost',
            )
        else:
            tenants = TenantApp.objects.filter(
                app__name__icontains='mattermost',
            )

        if not tenants.exists():
            raise CommandError(
                f'No Mattermost TenantApps found. {f"Tenant: {tenant_filter}" if tenant_filter else ""}'
            )

        for ta in tenants:
            try:
                extra = ta.extra_config or {}
                mm_url = extra.get('mattermost_url', '')
                team_id = extra.get('mm_team_id', '')

                if not mm_url or not team_id:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ {ta.tenant.schema_name}: Missing MM URL or team ID in extra_config'
                        )
                    )
                    continue

                self._add_bots_to_team(mm_url, headers, team_id)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ {ta.tenant.schema_name}: Bots added to team {team_id}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ {ta.tenant.schema_name}: {e}'
                    )
                )

    def _add_bots_to_team(self, mm_url: str, headers: dict, team_id: str) -> None:
        """Add all configured AI Peer bots to a team."""
        bot_usernames = [
            getattr(settings, 'BOT_USERNAME_SUPERGROK', 'supergrok'),
            getattr(settings, 'BOT_USERNAME_GEMINI', getattr(settings, 'BOT_USERNAME_GEM', 'gemini')),
            getattr(settings, 'BOT_USERNAME_WINDSURF', 'windsurf'),
            getattr(settings, 'BOT_USERNAME_CC', 'cc'),
            getattr(settings, 'BOT_USERNAME_ROUTER', 'router'),
            getattr(settings, 'BOT_USERNAME_OPENCLAW', 'openclaw'),
            getattr(settings, 'BOT_USERNAME_KIMI', 'kimi'),
            getattr(settings, 'BOT_USERNAME_WSC', 'wsc'),
        ]

        added, skipped, errors = [], [], []

        for bot_username in bot_usernames:
            try:
                # Resolve username → user ID
                r = requests.get(
                    f'{mm_url}/api/v4/users/username/{bot_username}',
                    headers=headers,
                    timeout=10,
                )
                if r.status_code != 200:
                    skipped.append(bot_username)
                    continue

                bot_user_id = r.json().get('id')
                if not bot_user_id:
                    skipped.append(bot_username)
                    continue

                # Add to team
                r2 = requests.post(
                    f'{mm_url}/api/v4/teams/{team_id}/members',
                    headers=headers,
                    json={'team_id': team_id, 'user_id': bot_user_id},
                    timeout=10,
                )
                if r2.status_code in (200, 201) or 'already' in r2.text.lower():
                    added.append(bot_username)
                else:
                    errors.append(f'{bot_username}:{r2.status_code}')
            except Exception as exc:
                errors.append(f'{bot_username}:{exc}')

        logger.info(
            'Bots added: %s=%s, skipped=%s, errors=%s',
            team_id,
            added,
            skipped,
            errors,
        )
