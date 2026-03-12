"""
Management command to configure Mattermost OIDC for local POL-5 testing.

Registers an OAuth2 Application in DOT for the given tenant, then PATCHes
the local Mattermost instance's OpenIdSettings via its admin API.

Usage:
  python manage.py setup_mattermost_oidc --tenant olient --mm-url http://localhost:8065

Prerequisites:
  1. Mattermost running (docker-compose -f docker-compose.mattermost.yml up -d)
  2. Mattermost admin user created (first user to sign up becomes admin)
  3. Admin personal access token created in Mattermost > Account Settings > Security
  4. Token stored in env: MATTERMOST_ADMIN_TOKEN=<token>
     Or passed via --mm-token <token>
"""
import os
import requests
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from oauth2_provider.models import Application
from dose.models import Tenant, TenantApp

User = get_user_model()


class Command(BaseCommand):
    help = 'Register OAuth2 app in DOT and configure Mattermost OIDC for a tenant'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', required=True, help='Tenant slug or schema_name')
        parser.add_argument('--mm-url', default='http://localhost:8065', help='Mattermost base URL')
        parser.add_argument('--mm-token', default='', help='Mattermost admin personal access token')
        parser.add_argument(
            '--polysaas-url', default='http://host.docker.internal:8000',
            help='PolySaaS base URL as seen from both browser and Mattermost container',
        )
        parser.add_argument('--dry-run', action='store_true', help='Show config without applying')

    def handle(self, *args, **options):
        tenant_slug = options['tenant']
        mm_url = options['mm_url'].rstrip('/')
        mm_token = options['mm_token'] or os.environ.get('MATTERMOST_ADMIN_TOKEN', '')
        polysaas_url = options['polysaas_url'].rstrip('/')
        dry_run = options['dry_run']

        # 1. Resolve tenant
        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            try:
                tenant = Tenant.objects.get(schema_name=tenant_slug)
            except Tenant.DoesNotExist:
                raise CommandError(f'Tenant "{tenant_slug}" not found')

        self.stdout.write(f'Tenant: {tenant.name} (schema={tenant.schema_name})')

        # 2. Get or create OAuth2 Application
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            raise CommandError('No superuser found — create one with createsuperuser first')

        app_name = f'{tenant.name}-mattermost'
        redirect_uri = f'{polysaas_url}/o/callback/'
        mm_redirect = f'{mm_url}/signup/openid/complete'

        oauth_app, created = Application.objects.get_or_create(
            name=app_name,
            defaults={
                'user': admin_user,
                'client_type': Application.CLIENT_CONFIDENTIAL,
                'authorization_grant_type': Application.GRANT_AUTHORIZATION_CODE,
                'redirect_uris': mm_redirect,
                'algorithm': 'RS256',
            },
        )
        if not created:
            oauth_app.redirect_uris = mm_redirect
            oauth_app.save(update_fields=['redirect_uris'])

        tenant_app, _ = TenantApp.objects.update_or_create(
            tenant=tenant,
            app_name='mattermost',
            defaults={
                'oauth_application': oauth_app,
                'app_url': mm_url,
                'status': 'provisioning',
            },
        )

        self.stdout.write(self.style.SUCCESS(
            f'OAuth2 App: {oauth_app.name}\n'
            f'  Client ID:     {oauth_app.client_id}\n'
            f'  Client Secret: {oauth_app.client_secret}\n'
            f'  Redirect URI:  {mm_redirect}'
        ))

        # 3. Build Mattermost OIDC config
        discovery_url = f'{polysaas_url}/o/.well-known/openid-configuration'

        oidc_config = {
            'OpenIdSettings': {
                'Enable': True,
                'Secret': oauth_app.client_secret,
                'Id': oauth_app.client_id,
                'DiscoveryEndpoint': discovery_url,
                'ButtonText': 'Log in with PolySaaS',
                'ButtonColor': '#003399',
            }
        }

        self.stdout.write(f'\nMattermost OIDC config:')
        self.stdout.write(f'  Discovery: {discovery_url}')
        self.stdout.write(f'  Button:    "Log in with PolySaaS"')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] — config not applied'))
            return

        if not mm_token:
            self.stdout.write(self.style.WARNING(
                '\nNo Mattermost admin token — skipping API config.\n'
                'Set MATTERMOST_ADMIN_TOKEN env var or use --mm-token.\n'
                'You can also paste the Client ID/Secret into System Console > OpenID Connect manually.'
            ))
            return

        # 4. PATCH Mattermost config
        self.stdout.write(f'\nConfiguring Mattermost at {mm_url}...')

        headers = {'Authorization': f'Bearer {mm_token}'}

        try:
            resp = requests.put(
                f'{mm_url}/api/v4/config/patch',
                headers=headers,
                json=oidc_config,
                timeout=15,
            )

            if resp.status_code == 200:
                tenant_app.status = 'active'
                tenant_app.save(update_fields=['status'])
                self.stdout.write(self.style.SUCCESS('Mattermost OIDC configured successfully!'))
                self.stdout.write(
                    f'\nPOL-5 test ready:\n'
                    f'  1. Log in to PolySaaS at {polysaas_url}\n'
                    f'  2. Open Mattermost at {mm_url}\n'
                    f'  3. Click "Log in with PolySaaS"\n'
                    f'  4. You should be logged in without entering MM credentials'
                )
            else:
                self.stdout.write(self.style.ERROR(
                    f'Mattermost API returned {resp.status_code}: {resp.text[:300]}'
                ))
        except requests.exceptions.ConnectionError:
            self.stdout.write(self.style.ERROR(
                f'Cannot reach Mattermost at {mm_url} — is it running?'
            ))
