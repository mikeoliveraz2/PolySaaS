"""
Synchronous Mattermost tenant provisioning.

Runs inline during subscription signup. Creates:
  1. MM team (name=schema, display=company)
  2. MM user account (email/username match Django user) — so OIDC login unifies
  3. Team membership (adds user to team)
  4. Personal access token for passthrough auth
  5. OIDC SSO config (if client_id/secret provided)
  6. PassThroughEndpoint row in tenant schema (sidebar entry)
  7. Welcome email

All steps are non-fatal except team creation — returns detailed result dict.
"""
from typing import Dict, Any, Optional
import logging
import secrets as _secrets

import requests

from dose.services.email_service import GmailEmailService
from dose.services.oauth2_registration import mark_tenant_app_active, mark_tenant_app_error

logger = logging.getLogger(__name__)

MATTERMOST_ADMIN_TOKEN_ENV = "MATTERMOST_ADMIN_TOKEN"
OIDC_DISCOVERY = "https://polysaas.online/o/.well-known/openid-configuration"


def _get_mattermost_base_url() -> str:
    """Mattermost origin (no path). Env wins, then Django settings; legacy default if unset."""
    import os
    from django.conf import settings
    url = (
        os.environ.get("MATTERMOST_URL", "").strip()
        or str(getattr(settings, "MATTERMOST_URL", "") or "").strip()
    ).rstrip("/")
    if not url:
        return "https://polysaas-mattermost.onrender.com"
    return url


def _get_admin_token() -> str:
    """Retrieve Mattermost admin personal access token from settings (uses sm() → Secret Manager or .env)."""
    from django.conf import settings
    return getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '')


def _create_team(mm_url: str, headers: dict, tenant_schema: str, display_name: str, result: dict) -> Optional[str]:
    name = tenant_schema[:64].lower()
    resp = requests.post(
        f"{mm_url}/api/v4/teams",
        headers=headers,
        json={"name": name, "display_name": display_name, "type": "I"},
        timeout=30,
    )
    if resp.status_code == 201:
        team = resp.json()
        result['team_id'] = team['id']
        result['team_name'] = team['name']
        logger.info("[MM-PROV] Created team %s (id=%s)", name, team['id'])
        return team['id']
    if resp.status_code == 400 and 'already exists' in resp.text.lower():
        existing = requests.get(f"{mm_url}/api/v4/teams/name/{name}", headers=headers, timeout=15)
        if existing.status_code == 200:
            team = existing.json()
            result['team_id'] = team['id']
            result['team_name'] = team['name']
            result['team_existed'] = True
            logger.info("[MM-PROV] Team %s already exists (id=%s)", name, team['id'])
            return team['id']
    logger.error("[MM-PROV] Team creation failed: %s %s", resp.status_code, resp.text[:300])
    result['team_error'] = resp.text[:300]
    return None


def _create_user(mm_url: str, headers: dict, admin_email: str, username: str, password: str, result: dict) -> Optional[str]:
    if not password:
        password = _secrets.token_urlsafe(16)
        result['generated_password'] = True
    resp = requests.post(
        f"{mm_url}/api/v4/users",
        headers=headers,
        json={'email': admin_email, 'username': username, 'password': password},
        timeout=30,
    )
    if resp.status_code == 201:
        mm_user = resp.json()
        result['mm_user_id'] = mm_user['id']
        result['mm_username'] = mm_user['username']
        logger.info("[MM-PROV] Created user %s (id=%s)", username, mm_user['id'])
        return mm_user['id']
    if resp.status_code == 400 and 'already exists' in resp.text.lower():
        existing = requests.get(
            f"{mm_url}/api/v4/users/username/{username.lower()}",
            headers=headers, timeout=15,
        )
        if existing.status_code == 200:
            mm_user = existing.json()
            result['mm_user_id'] = mm_user['id']
            result['mm_username'] = mm_user['username']
            result['user_existed'] = True
            logger.info("[MM-PROV] User %s already exists (id=%s)", username, mm_user['id'])
            return mm_user['id']
    logger.error("[MM-PROV] User creation failed: %s %s", resp.status_code, resp.text[:300])
    result['user_error'] = resp.text[:300]
    return None


def _add_user_to_team(mm_url: str, headers: dict, team_id: str, user_id: str, result: dict) -> None:
    resp = requests.post(
        f"{mm_url}/api/v4/teams/{team_id}/members",
        headers=headers,
        json={'team_id': team_id, 'user_id': user_id},
        timeout=15,
    )
    if resp.status_code in (200, 201):
        result['team_member'] = True
        logger.info("[MM-PROV] Added user %s to team %s", user_id, team_id)
    elif 'already' in resp.text.lower():
        result['team_member'] = True
        result['team_member_existed'] = True
    else:
        logger.warning("[MM-PROV] Team membership failed: %s", resp.text[:200])
        result['team_member_error'] = resp.text[:200]


def _create_user_token(mm_url: str, headers: dict, user_id: str, result: dict) -> Optional[str]:
    resp = requests.post(
        f"{mm_url}/api/v4/users/{user_id}/tokens",
        headers=headers,
        json={'description': 'PolySaaS passthrough token'},
        timeout=15,
    )
    if resp.status_code in (200, 201):
        token_data = resp.json()
        result['mm_token_id'] = token_data.get('id', '')
        logger.info("[MM-PROV] Created access token for user %s", user_id)
        return token_data.get('token', '')
    logger.warning("[MM-PROV] Token creation failed: %s", resp.text[:200])
    result['token_error'] = resp.text[:200]
    return None


def _configure_oidc(mm_url: str, headers: dict, client_id: str, client_secret: str, result: dict) -> bool:
    resp = requests.put(
        f"{mm_url}/api/v4/config/patch",
        headers=headers,
        json={
            "OpenIdSettings": {
                "Enable": True,
                "Secret": client_secret,
                "Id": client_id,
                "DiscoveryEndpoint": OIDC_DISCOVERY,
                "ButtonText": "Log in with PolySaaS",
                "ButtonColor": "#003399",
            }
        },
        timeout=30,
    )
    if resp.status_code == 200:
        logger.info("[MM-PROV] Configured OIDC SSO")
        result['oidc_enabled'] = True
        return True
    logger.warning("[MM-PROV] OIDC config returned %s: %s", resp.status_code, resp.text[:200])
    result['oidc_error'] = resp.text[:200]
    return False


def _ensure_passthrough_endpoint(tenant_schema: str, mm_url: str, result: dict) -> None:
    try:
        from django.db import connection
        from urllib.parse import urlparse
        from dose.models import PassThroughEndpoint
        hostname = urlparse(mm_url).netloc
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{tenant_schema}", public')
        _, created = PassThroughEndpoint.objects.update_or_create(
            slug='mattermost',
            defaults={
                'name': 'Mattermost',
                'endpoint_url': mm_url,
                'description': 'Mattermost Team Chat - tenant-specific team',
                'is_enabled': True,
                'passthrough_type': 'scraper',
                'integration_mode': 'web_api',
                'api_endpoint': f"{mm_url}/api/v4",
                'show_in_menu': True,
                'menu_title': 'Mattermost',
                'menu_icon': 'chat',
                'menu_sort_order': 25,
                'starting_uri': '/',
            },
        )
        result['passthrough_endpoint_created' if created else 'passthrough_endpoint_updated'] = True
    except Exception as e:
        logger.warning("[MM-PROV] PassThroughEndpoint upsert failed: %s", e)
        result['passthrough_endpoint_error'] = str(e)


def _store_credentials(tenant_app_id: int, mm_url: str, token: str, mm_user_id: str,
                       username: str, password: str, team_id: str, oidc_enabled: bool) -> None:
    if not tenant_app_id:
        return
    try:
        from dose.models import TenantApp
        ta = TenantApp.objects.filter(id=tenant_app_id).first()
        if not ta:
            return
        cfg = ta.extra_config or {}
        cfg['mattermost_url'] = mm_url
        cfg['mattermost_oidc_enabled'] = oidc_enabled
        if token:
            cfg['mm_token'] = token
            cfg['mmauthtoken'] = token
        if mm_user_id:
            cfg['mm_user_id'] = mm_user_id
        if username:
            cfg['mm_login_id'] = username
            cfg['mattermost_login_id'] = username
            cfg['mattermost_username'] = username
        if password:
            cfg['mm_password'] = password
            cfg['mattermost_password'] = password
        if team_id:
            cfg['mm_team_id'] = team_id
        ta.extra_config = cfg
        ta.save(update_fields=['extra_config'])
        mark_tenant_app_active(ta, app_url=mm_url)
    except Exception as e:
        logger.warning("[MM-PROV] Credential persist failed: %s", e)


def _send_welcome_email(admin_email: str, mm_url: str, display_name: str) -> None:
    try:
        email_svc = GmailEmailService(credentials_file='gmail_creds.json')
        body = f"""
        <h2>Your PolySaaS tenant is live, and Mattermost is ready!</h2>
        <p><strong>Chat URL:</strong> <a href="{mm_url}">{mm_url}</a></p>
        <p><strong>How to log in:</strong> Click "Log in with PolySaaS" on the Mattermost login page.
        You'll be signed in automatically with your PolySaaS account.</p>
        <p>Your team (<strong>{display_name}</strong>) is already set up and waiting for you.</p>
        <p>Welcome to PolySaaS!</p>
        """
        email_svc.send_email(
            to_email=admin_email,
            subject="Welcome to PolySaaS + Mattermost",
            body=body,
        )
    except Exception as e:
        logger.warning("[MM-PROV] Welcome email failed: %s", e)


def provision_mattermost_tenant(
    tenant_schema: str,
    tenant_name: str,
    admin_email: str,
    company_name: str,
    oauth_client_id: str = '',
    oauth_client_secret: str = '',
    tenant_app_id: int = None,
    admin_username: str = '',
    admin_password: str = '',
) -> Dict[str, Any]:
    """Complete, synchronous Mattermost tenant provisioning. Called directly from signup."""
    admin_token = _get_admin_token()
    if not admin_token:
        msg = "MATTERMOST_ADMIN_TOKEN not configured"
        logger.error("[MM-PROV] %s", msg)
        if tenant_app_id:
            try:
                from dose.models import TenantApp
                ta = TenantApp.objects.filter(id=tenant_app_id).first()
                if ta:
                    mark_tenant_app_error(ta, msg)
            except Exception:
                pass
        return {'success': False, 'error': msg}

    headers = {"Authorization": f"Bearer {admin_token}"}
    mm_url = _get_mattermost_base_url()
    display_name = company_name or tenant_name
    username = (admin_username or admin_email.split('@')[0]).lower()[:64]

    result: Dict[str, Any] = {
        'tenant_schema': tenant_schema,
        'tenant_name': tenant_name,
        'admin_email': admin_email,
        'mm_url': mm_url,
    }

    try:
        _ensure_passthrough_endpoint(tenant_schema, mm_url, result)

        team_id = _create_team(mm_url, headers, tenant_schema, display_name, result)
        if not team_id:
            result['success'] = False
            result['error'] = 'Team creation failed (endpoint still created)'
            return result

        user_id = _create_user(mm_url, headers, admin_email, username, admin_password, result)
        token = ''
        if user_id:
            _add_user_to_team(mm_url, headers, team_id, user_id, result)
            token = _create_user_token(mm_url, headers, user_id, result) or ''

        oidc_enabled = False
        if oauth_client_id and oauth_client_secret:
            oidc_enabled = _configure_oidc(mm_url, headers, oauth_client_id, oauth_client_secret, result)

        _store_credentials(
            tenant_app_id, mm_url, token, user_id or '',
            username, admin_password, team_id, oidc_enabled,
        )

        _send_welcome_email(admin_email, mm_url, display_name)

        result['success'] = True
        result['oidc_enabled'] = oidc_enabled
        result['message'] = 'Mattermost tenant provisioned'
        logger.info("[MM-PROV] Success for %s (team=%s user=%s)", tenant_schema, team_id, user_id)
        return result

    except Exception as exc:
        logger.error("[MM-PROV] Failed for %s: %s", tenant_schema, exc, exc_info=True)
        if tenant_app_id:
            try:
                from dose.models import TenantApp
                ta = TenantApp.objects.filter(id=tenant_app_id).first()
                if ta:
                    mark_tenant_app_error(ta, str(exc))
            except Exception:
                pass
        result['success'] = False
        result['error'] = str(exc)
        return result
