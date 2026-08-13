"""
MattermostProvisioning — Atomic Service for provisioning a Mattermost
team + admin user when a tenant subscribes to the Mattermost bundled app.

Data-driven: reads Mattermost URL and admin token from the Parameters model
(matchingKey = 'MattermostProvisioning'). No hardcoded config.

Triggered via an Instruction matching the subscription event. The Instruction's
executescript field should be set to 'MattermostProvisioning'.

Parameters (configured in admin):
  param1 = Mattermost base URL  (e.g. http://localhost:8065)
  param2 = Mattermost admin personal access token
  param3 = Team type            (I = invite-only, O = open; default I)

  Superuser optional encrypted JSON on the same row (replaces param1–param3 when keys present):
  mm_url, admin_token, team_type (aliases: MM_URL, MATTERMOST_ADMIN_TOKEN, TEAM_TYPE).
"""
import json
import logging

import requests as http_requests
from django.conf import settings

from dose.services.atomic_service_base import AtomicServiceBase
from dose.services.atomic_services_registry import filter_parameters_for_service

logger = logging.getLogger(__name__)


class MattermostProvisioning(AtomicServiceBase):

    @staticmethod
    def get_parameters(parameters, key='MattermostProvisioning'):
        filtered = filter_parameters_for_service(parameters, key)
        if filtered is not None:
            return filtered
        if isinstance(parameters, dict):
            return parameters if parameters.get('matchingKey') == key else None
        return None

    @staticmethod
    def execute_and_save(request, instruction_row):
        tenant = getattr(request, 'tenant', None)
        user = getattr(request, 'user', None)
        params = getattr(request, 'atomic_parameters', [])

        if not tenant:
            msg = 'No tenant on request — cannot provision Mattermost'
            logger.error('[MM-PROVISION] %s', msg)
            return {'success': False, 'error': msg}

        config = MattermostProvisioning._load_config(params)
        if not config:
            msg = 'Missing Parameters for MattermostProvisioning'
            logger.error('[MM-PROVISION] %s', msg)
            return {'success': False, 'error': msg}

        mm_url = config['mm_url']
        admin_token = config['admin_token']
        team_type = config.get('team_type', 'I')

        headers = {'Authorization': f'Bearer {admin_token}'}
        result = {
            'tenant': tenant.name,
            'schema': getattr(tenant, 'schema_name', ''),
            'user_email': getattr(user, 'email', ''),
        }

        try:
            team_id = MattermostProvisioning._create_team(
                mm_url, headers, tenant, team_type, result,
            )
            user_id = MattermostProvisioning._create_user(
                mm_url, headers, user, result, request=request,
            )
            if team_id and user_id:
                MattermostProvisioning._add_user_to_team(
                    mm_url, headers, team_id, user_id, result,
                )
                token = MattermostProvisioning._create_user_token(
                    mm_url, headers, user_id, result,
                )
                # Pass username + password for passthrough auto-login
                mm_username = (user.username if user else '') or ''
                mm_password = (
                    getattr(user, '_plaintext_password', None)
                    or (request.POST.get('password') if request and hasattr(request, 'POST') else None)
                    or getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!')
                    or ''
                )
                MattermostProvisioning._store_credentials(
                    tenant, token, result,
                    mm_username=mm_username,
                    mm_password=mm_password,
                )

            result['success'] = True
            result['message'] = 'Mattermost tenant provisioned'
            logger.info('[MM-PROVISION] Success for %s', tenant.name)

        except Exception as exc:
            result['success'] = False
            result['error'] = str(exc)
            logger.error('[MM-PROVISION] Failed for %s: %s', tenant.name, exc)

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_config(params):
        for p in (params or []):
            key = getattr(p, 'matchingKey', '') if hasattr(p, 'matchingKey') else ''
            if key != 'MattermostProvisioning':
                continue
            secrets = {}
            if hasattr(p, 'get_decrypted_secrets'):
                secrets = p.get_decrypted_secrets() or {}
            mm_url = (
                (secrets.get('mm_url') or secrets.get('MM_URL') or getattr(p, 'param1', '') or '')
            ).strip()
            admin_token = (
                (
                    secrets.get('admin_token')
                    or secrets.get('MATTERMOST_ADMIN_TOKEN')
                    or getattr(p, 'param2', '')
                    or ''
                )
            ).strip()
            team_type = (
                (secrets.get('team_type') or secrets.get('TEAM_TYPE') or getattr(p, 'param3', '') or 'I')
                .strip()
                or 'I'
            )
            if mm_url and admin_token:
                return {
                    'mm_url': mm_url.rstrip('/'),
                    'admin_token': admin_token,
                    'team_type': team_type,
                }
        return None

    @staticmethod
    def _create_team(mm_url, headers, tenant, team_type, result):
        schema = getattr(tenant, 'schema_name', tenant.name).lower()[:64]
        display = tenant.name

        resp = http_requests.post(
            f'{mm_url}/api/v4/teams',
            headers=headers,
            json={'name': schema, 'display_name': display, 'type': team_type},
            timeout=30,
        )

        if resp.status_code == 201:
            team = resp.json()
            result['team_id'] = team['id']
            result['team_name'] = team['name']
            logger.info('[MM-PROVISION] Created team %s (id=%s)', schema, team['id'])
            return team['id']

        if resp.status_code == 400 and 'already exists' in resp.text.lower():
            existing = http_requests.get(
                f'{mm_url}/api/v4/teams/name/{schema}',
                headers=headers, timeout=15,
            )
            if existing.status_code == 200:
                team = existing.json()
                result['team_id'] = team['id']
                result['team_name'] = team['name']
                result['team_existed'] = True
                logger.info('[MM-PROVISION] Team %s already exists (id=%s)', schema, team['id'])
                return team['id']

        logger.error('[MM-PROVISION] Team creation failed: %s %s', resp.status_code, resp.text[:300])
        result['team_error'] = resp.text[:300]
        return None

    @staticmethod
    def _create_user(mm_url, headers, django_user, result, request=None):
        if not django_user:
            return None

        email = django_user.email
        username = django_user.username
        password = getattr(django_user, '_plaintext_password', None)
        if not password and request and hasattr(request, 'POST'):
            password = request.POST.get('password') or request.POST.get('password1')
        if not password:
            import secrets
            password = secrets.token_urlsafe(16)
            result['generated_password'] = True

        user_data = {
            'email': email,
            'username': username,
            'password': password,
        }

        resp = http_requests.post(
            f'{mm_url}/api/v4/users',
            headers=headers,
            json=user_data,
            timeout=30,
        )

        if resp.status_code == 201:
            mm_user = resp.json()
            result['mm_user_id'] = mm_user['id']
            result['mm_username'] = mm_user['username']
            logger.info('[MM-PROVISION] Created user %s (id=%s)', username, mm_user['id'])
            return mm_user['id']

        if resp.status_code == 400 and 'already exists' in resp.text.lower():
            mm_username = username.lower()
            existing = http_requests.get(
                f'{mm_url}/api/v4/users/username/{mm_username}',
                headers=headers, timeout=15,
            )
            if existing.status_code == 200:
                mm_user = existing.json()
                result['mm_user_id'] = mm_user['id']
                result['mm_username'] = mm_user['username']
                result['user_existed'] = True
                logger.info('[MM-PROVISION] User %s already exists (id=%s)', username, mm_user['id'])
                return mm_user['id']

        logger.error('[MM-PROVISION] User creation failed: %s %s', resp.status_code, resp.text[:300])
        result['user_error'] = resp.text[:300]
        return None

    @staticmethod
    def _add_user_to_team(mm_url, headers, team_id, user_id, result):
        resp = http_requests.post(
            f'{mm_url}/api/v4/teams/{team_id}/members',
            headers=headers,
            json={'team_id': team_id, 'user_id': user_id},
            timeout=15,
        )
        if resp.status_code in (200, 201):
            result['team_member'] = True
            logger.info('[MM-PROVISION] Added user %s to team %s', user_id, team_id)
        elif 'already' in resp.text.lower():
            result['team_member'] = True
            result['team_member_existed'] = True
        else:
            logger.warning('[MM-PROVISION] Team membership failed: %s', resp.text[:200])
            result['team_member_error'] = resp.text[:200]

    @staticmethod
    def _create_user_token(mm_url, headers, user_id, result):
        """Create a personal access token for the provisioned user."""
        resp = http_requests.post(
            f'{mm_url}/api/v4/users/{user_id}/tokens',
            headers=headers,
            json={'description': 'PolySaaS passthrough token'},
            timeout=15,
        )
        if resp.status_code in (200, 201):
            token_data = resp.json()
            result['mm_token_id'] = token_data.get('id', '')
            logger.info('[MM-PROVISION] Created access token for user %s', user_id)
            return token_data.get('token', '')
        else:
            logger.warning('[MM-PROVISION] Token creation failed: %s', resp.text[:200])
            result['token_error'] = resp.text[:200]
            return None

    @staticmethod
    def _store_credentials(tenant, token, result, mm_username='', mm_password=''):
        """Store the Mattermost token and login credentials on TenantApp.extra_config for passthrough auth."""
        try:
            from dose.models import TenantApp
            ta = TenantApp.objects.filter(
                tenant=tenant, app_name='mattermost',
            ).first()
            if ta:
                cfg = ta.extra_config or {}
                if token:
                    cfg['mm_token'] = token
                if mm_username:
                    cfg['mm_login_id'] = mm_username
                if mm_password:
                    cfg['mm_password'] = mm_password
                ta.extra_config = cfg
                ta.save(update_fields=['extra_config'])
                result['credentials_stored'] = True
                logger.info('[MM-PROVISION] Stored credentials on TenantApp for %s', tenant.name)
        except Exception as exc:
            logger.warning('[MM-PROVISION] Could not store credentials: %s', exc)
            result['credentials_error'] = str(exc)
