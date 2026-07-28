# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Production Preview demo — shared Town Square landing + honest provision — 2026-06-15
"""
Synchronous Mattermost tenant provisioning.

Runs inline during subscription signup. Creates:
  1. Private MM team (company name — tenant-owned; future company members join here)
  2. Shared MM team (polysaas-dev-team — AI peers + cross-subscriber collaboration)
  3. MM user account (email/username match Django user) — so OIDC login unifies
  4. Team membership on BOTH teams
  5. Personal access token for passthrough auth
  6. OIDC SSO config (if client_id/secret provided)
  7. PassThroughEndpoint row in tenant schema (sidebar entry)
  8. Welcome email

All steps are non-fatal except team creation — returns detailed result dict.
"""
from typing import Dict, Any, Optional
import logging
import re
import secrets as _secrets
from pathlib import Path

import requests

from dose.services.email_to import GmailEmail
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


def _get_default_app_password() -> str:
    from django.conf import settings

    return getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!') or 'PolySaaS2026!'


def _shared_team_name() -> str:
    """Mattermost team slug for shared Town Square (all demo/subscriber users)."""
    import os
    from django.conf import settings

    return (
        os.environ.get('MATTERMOST_SHARED_TEAM_NAME', '').strip()
        or str(getattr(settings, 'MATTERMOST_SHARED_TEAM_NAME', '') or '').strip()
        or 'polysaas-dev-team'
    )


def _shared_team_display_name() -> str:
    import os
    from django.conf import settings

    return (
        os.environ.get('MATTERMOST_SHARED_TEAM_DISPLAY_NAME', '').strip()
        or str(getattr(settings, 'MATTERMOST_SHARED_TEAM_DISPLAY_NAME', '') or '').strip()
        or 'PolySaaS Dev Team'
    )


def _get_admin_token() -> str:
    """Retrieve Mattermost admin personal access token from settings (uses sm() → Secret Manager or .env)."""
    env_path = Path(__file__).resolve().parents[2] / '.env'
    if env_path.exists():
        try:
            for raw_line in env_path.read_text(encoding='utf-8').splitlines():
                line = raw_line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                if key.strip() == 'MATTERMOST_ADMIN_TOKEN':
                    return value.strip().strip('"').strip("'")
        except Exception:
            pass
    from django.conf import settings
    token = getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '')
    return token.strip() if token else ''


def _verify_token(mm_url: str, headers: dict) -> bool:
    """Quick sanity check that the admin token is valid."""
    try:
        resp = requests.get(f"{mm_url}/api/v4/users/me", headers=headers, timeout=10)
        if resp.status_code == 200:
            user = resp.json()
            logger.info("[MM-PROV] Token OK — admin user %s (roles=%s)", user.get('username'), user.get('roles', '')[:100])
            return True
        logger.error("[MM-PROV] Token verification failed: HTTP %s — %s", resp.status_code, resp.text[:200])
        return False
    except Exception as exc:
        logger.error("[MM-PROV] Token verification exception: %s", exc)
        return False


def _create_team(mm_url: str, headers: dict, tenant_schema: str, display_name: str, result: dict) -> Optional[str]:
    # First verify token works
    if not _verify_token(mm_url, headers):
        result['team_error'] = "Admin token verification failed — check MATTERMOST_ADMIN_TOKEN"
        return None

    # Use company name for team name, convert to Mattermost URL-friendly format
    # Mattermost team names: lowercase, spaces to hyphens, max 64 chars, only a-z 0-9 - _
    raw_team_name = display_name.lower()
    # Replace spaces with hyphens
    team_name = re.sub(r'\s+', '-', raw_team_name)
    # Remove invalid characters (keep only a-z, 0-9, -, _)
    team_name = re.sub(r'[^a-z0-9\-_]', '', team_name)
    # Ensure it starts with a letter
    team_name = re.sub(r'^[^a-z]+', '', team_name)
    # Limit to 64 chars
    team_name = team_name[:64]
    # Ensure at least 2 chars
    if len(team_name) < 2:
        team_name = "team"

    logger.info("[MM-PROV] Creating team from company name=%r display_name=%r for tenant=%s", team_name, display_name, tenant_schema)

    resp = requests.post(
        f"{mm_url}/api/v4/teams",
        headers=headers,
        json={"name": team_name, "display_name": display_name, "type": "O"},
        timeout=30,
    )
    if resp.status_code == 201:
        team = resp.json()
        result['team_id'] = team['id']
        result['team_name'] = team['name']
        logger.info("[MM-PROV] Created team %s (id=%s)", team_name, team['id'])
        return team['id']
    if resp.status_code == 400 and 'already exists' in resp.text.lower():
        existing = requests.get(f"{mm_url}/api/v4/teams/name/{team_name}", headers=headers, timeout=15)
        if existing.status_code == 200:
            team = existing.json()
            result['team_id'] = team['id']
            result['team_name'] = team['name']
            result['team_existed'] = True
            logger.info("[MM-PROV] Team %s already exists (id=%s)", team_name, team['id'])
            return team['id']
    # Log FULL response for debugging
    logger.error("[MM-PROV] Team creation failed: HTTP %s body=%s", resp.status_code, resp.text)
    result['team_error'] = f"HTTP {resp.status_code}: {resp.text[:500]}"
    return None


def _generate_strong_password() -> str:
    """Generate a password meeting Mattermost default requirements (8+ chars, upper, lower, number, symbol)."""
    import string, random
    chars = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*"),
    ]
    chars += random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=12)
    random.shuffle(chars)
    return ''.join(chars)


def _create_user(mm_url: str, headers: dict, admin_email: str, username: str, password: str, result: dict) -> Optional[str]:
    if not password:
        password = _generate_strong_password()
        result['generated_password'] = True
    result['mm_effective_password'] = password
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
        if admin_email and 'email_exists' in resp.text.lower():
            by_email = requests.get(
                f"{mm_url}/api/v4/users/email/{admin_email}",
                headers=headers,
                timeout=15,
            )
            if by_email.status_code == 200:
                mm_user = by_email.json()
                result['mm_user_id'] = mm_user['id']
                result['mm_username'] = mm_user['username']
                result['user_existed'] = True
                result['user_linked_by_email'] = True
                logger.info(
                    "[MM-PROV] Linked existing MM user @%s by email %s (id=%s)",
                    mm_user.get('username'), admin_email, mm_user['id'],
                )
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


def _town_square_channel_id(mm_url: str, headers: dict, team_id: str) -> Optional[str]:
    """Return town-square channel id for a team, or None."""
    try:
        resp = requests.get(
            f"{mm_url.rstrip('/')}/api/v4/teams/{team_id}/channels/name/town-square",
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get('id') or None
    except Exception as exc:
        logger.warning("[MM-PROV] town-square lookup failed for team %s: %s", team_id, exc)
    return None


def set_mattermost_shared_team_landing(
    mm_url: str,
    headers: dict,
    user_id: str,
    shared_team_id: str,
    result: Optional[dict] = None,
) -> bool:
    """
    Set Mattermost user preferences so the SPA opens the shared team's Town Square
    (where AI peers live). Uses preference category 'last' / names 'team' and 'channel'.
    """
    if not user_id or not shared_team_id:
        return False
    channel_id = _town_square_channel_id(mm_url, headers, shared_team_id)
    if not channel_id:
        if result is not None:
            result['shared_landing_error'] = 'town-square not found on shared team'
        return False

    prefs = [
        {'user_id': user_id, 'category': 'last', 'name': 'team', 'value': shared_team_id},
        {'user_id': user_id, 'category': 'last', 'name': 'channel', 'value': channel_id},
    ]
    try:
        resp = requests.put(
            f"{mm_url.rstrip('/')}/api/v4/users/{user_id}/preferences",
            headers=headers,
            json=prefs,
            timeout=15,
        )
        if resp.status_code == 200:
            logger.info(
                "[MM-PROV] Shared Town Square landing set for user %s (team=%s channel=%s)",
                user_id, shared_team_id, channel_id,
            )
            if result is not None:
                result['shared_landing_set'] = True
            return True
        logger.warning(
            "[MM-PROV] Shared landing preferences failed HTTP %s: %s",
            resp.status_code, resp.text[:200],
        )
        if result is not None:
            result['shared_landing_error'] = resp.text[:200]
    except Exception as exc:
        logger.warning("[MM-PROV] Shared landing preferences exception: %s", exc)
        if result is not None:
            result['shared_landing_error'] = str(exc)
    return False


def sync_mattermost_users_shared_team_landing(
    mm_url: str,
    headers: dict,
    shared_team_id: str,
    *,
    tenant_schemas: Optional[list] = None,
    log=None,
) -> dict:
    """
    Set shared-team Town Square as the MM landing for all provisioned tenant users.
    Pass tenant_schemas to limit scope (e.g. demo tenants only).
    """
    from dose.models import TenantApp

    mm_url = mm_url.rstrip('/')
    stats = {'updated': 0, 'skipped': 0, 'errors': 0}
    seen_users: set = set()

    qs = TenantApp.public_bundles.filter(app_name__icontains='mattermost')
    if tenant_schemas:
        qs = qs.filter(tenant__schema_name__in=tenant_schemas)

    for ta in qs.select_related('tenant'):
        uid = ((ta.extra_config or {}).get('mm_user_id') or '').strip()
        if not uid:
            stats['skipped'] += 1
            continue
        if uid in seen_users:
            stats['skipped'] += 1
            continue
        seen_users.add(uid)
        try:
            ok = set_mattermost_shared_team_landing(mm_url, headers, uid, shared_team_id)
            if ok:
                stats['updated'] += 1
                schema = getattr(ta.tenant, 'schema_name', '?')
                if log:
                    log(f"  landing -> shared Town Square for MM user {uid} ({schema})")
            else:
                stats['errors'] += 1
        except Exception as exc:
            stats['errors'] += 1
            logger.warning("[MM-PROV] Landing sync failed for user %s: %s", uid, exc)

    return stats


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


def _ensure_system_admin_user(mm_url: str, headers: dict, result: dict) -> Optional[str]:
    """Create or ensure a system admin user (mmadmin) exists and has system admin role."""
    admin_username = 'mmadmin'
    admin_password = 'PolySaaS2026!'
    admin_email = f'{admin_username}@polysaas.local'
    
    # Check if user already exists
    try:
        resp = requests.get(f"{mm_url}/api/v4/users/username/{admin_username}", headers=headers, timeout=10)
        if resp.status_code == 200:
            user = resp.json()
            logger.info("[MM-PROV] System admin user already exists: %s", admin_username)
            # Ensure user has system admin role
            _promote_to_system_admin(mm_url, headers, user['id'], result)
            return user['id']
    except Exception as e:
        logger.warning("[MM-PROV] Error checking for system admin user: %s", e)
    
    # Create the system admin user
    try:
        resp = requests.post(
            f"{mm_url}/api/v4/users",
            headers=headers,
            json={
                'email': admin_email,
                'username': admin_username,
                'password': admin_password,
                'first_name': 'PolySaaS',
                'last_name': 'Admin'
            },
            timeout=30,
        )
        if resp.status_code == 201:
            user = resp.json()
            logger.info("[MM-PROV] Created system admin user: %s (id=%s)", admin_username, user['id'])
            result['system_admin_user_created'] = True
            # Promote to system admin
            _promote_to_system_admin(mm_url, headers, user['id'], result)
            return user['id']
        else:
            logger.error("[MM-PROV] Failed to create system admin user: %s - %s", resp.status_code, resp.text[:200])
            result['system_admin_error'] = resp.text[:200]
            return None
    except Exception as e:
        logger.error("[MM-PROV] Exception creating system admin user: %s", e)
        result['system_admin_error'] = str(e)
        return None


def _promote_to_system_admin(mm_url: str, headers: dict, user_id: str, result: dict) -> bool:
    """Promote a user to system admin role."""
    try:
        # Get current user roles
        resp = requests.get(f"{mm_url}/api/v4/users/{user_id}", headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.error("[MM-PROV] Failed to get user for promotion: %s", resp.text[:200])
            return False
        
        user = resp.json()
        current_roles = user.get('roles', '')
        
        # Add system_admin role if not present
        if 'system_admin' not in current_roles:
            new_roles = current_roles + ' system_admin' if current_roles else 'system_admin'
            patch_resp = requests.put(
                f"{mm_url}/api/v4/users/{user_id}/roles",
                headers=headers,
                json={'roles': new_roles},
                timeout=30,
            )
            if patch_resp.status_code == 200:
                logger.info("[MM-PROV] Promoted user %s to system admin", user_id)
                result['system_admin_promoted'] = True
                return True
            else:
                logger.error("[MM-PROV] Failed to promote user to system admin: %s", patch_resp.text[:200])
                result['system_admin_promote_error'] = patch_resp.text[:200]
                return False
        else:
            logger.info("[MM-PROV] User %s already has system admin role", user_id)
            return True
    except Exception as e:
        logger.error("[MM-PROV] Exception promoting user to system admin: %s", e)
        result['system_admin_promote_error'] = str(e)
        return False


def _ensure_dev_team(mm_url: str, headers: dict, result: dict) -> Optional[str]:
    """Create or ensure the shared collaboration team exists (Town Square for all subscribers)."""
    team_name = _shared_team_name()
    team_display_name = _shared_team_display_name()
    
    # Check if team already exists
    try:
        resp = requests.get(f"{mm_url}/api/v4/teams/name/{team_name}", headers=headers, timeout=10)
        if resp.status_code == 200:
            team = resp.json()
            logger.info("[MM-PROV] Dev team already exists: %s", team_name)
            result['dev_team_id'] = team['id']
            result['team_name'] = team_name
            return team['id']
    except Exception as e:
        logger.warning("[MM-PROV] Error checking for dev team: %s", e)
    
    # Create the dev team
    try:
        resp = requests.post(
            f"{mm_url}/api/v4/teams",
            headers=headers,
            json={
                'name': team_name,
                'display_name': team_display_name,
                'type': 'O'  # Open team
            },
            timeout=30,
        )
        if resp.status_code == 201:
            team = resp.json()
            logger.info("[MM-PROV] Created dev team: %s (id=%s)", team_name, team['id'])
            result['dev_team_created'] = True
            result['dev_team_id'] = team['id']
            result['team_name'] = team_name
            return team['id']
        else:
            logger.error("[MM-PROV] Failed to create dev team: %s - %s", resp.status_code, resp.text[:200])
            result['dev_team_error'] = resp.text[:200]
            return None
    except Exception as e:
        logger.error("[MM-PROV] Exception creating dev team: %s", e)
        result['dev_team_error'] = str(e)
        return None


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


def _store_credentials(
    tenant_app_id: int,
    mm_url: str,
    token: str,
    mm_user_id: str,
    username: str,
    password: str,
    team_id: str,
    team_name: str,
    oidc_enabled: bool,
    *,
    shared_team_id: str = '',
    shared_team_name: str = '',
) -> None:
    if not tenant_app_id:
        return
    try:
        from django.db import connection
        from dose.models import TenantApp
        ta = TenantApp.public_bundles.filter(id=tenant_app_id).first()
        if not ta:
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
        if team_name:
            cfg['mm_team_name'] = team_name
        if shared_team_id:
            cfg['mm_shared_team_id'] = shared_team_id
        if shared_team_name:
            cfg['mm_shared_team_name'] = shared_team_name
        with connection.cursor() as cursor:
            cursor.execute('SET search_path TO public,pg_catalog')
        ta.extra_config = cfg
        ta.save(update_fields=['extra_config'])
        if mm_user_id:
            mark_tenant_app_active(ta, app_url=mm_url)
        else:
            mark_tenant_app_error(ta, 'Mattermost user id missing after provisioning')
    except Exception as e:
        logger.warning("[MM-PROV] Credential persist failed: %s", e)


def resolve_shared_mattermost_team_id(mm_url: str, headers: dict) -> Optional[str]:
    """Look up the shared collaboration team ID by configured slug."""
    team_name = _shared_team_name()
    try:
        resp = requests.get(
            f"{mm_url.rstrip('/')}/api/v4/teams/name/{team_name}",
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get('id') or None
    except Exception as exc:
        logger.warning("[MM-PROV] Shared team lookup failed: %s", exc)
    return None


def _send_welcome_email(admin_email: str, mm_url: str, display_name: str) -> None:
    try:
        email_svc = GmailEmail(credentials_file='gmail_creds.json')
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
    # Mattermost usernames must start with a letter, contain only lowercase a-z, 0-9, ., -, _
    raw_username = (admin_username or admin_email.split('@')[0]).lower()[:64]
    # Ensure it starts with a letter
    username = re.sub(r'^[^a-z]+', '', raw_username)
    # Remove invalid characters
    username = re.sub(r'[^a-z0-9._-]', '', username)
    if not username:
        username = 'user'
    # Ensure at least 3 chars for Mattermost
    if len(username) < 3:
        username = username + '001'
    username = username[:64]

    result: Dict[str, Any] = {
        'tenant_schema': tenant_schema,
        'tenant_name': tenant_name,
        'admin_email': admin_email,
        'mm_url': mm_url,
    }
    effective_password = admin_password or _get_default_app_password()

    try:
        _ensure_passthrough_endpoint(tenant_schema, mm_url, result)

        # Private company team — tenant-owned workspace for their org
        company_team_id = _create_team(mm_url, headers, tenant_schema, display_name, result)
        if not company_team_id:
            result['success'] = False
            detail = result.get('team_error') or 'unknown'
            result['error'] = f'Company Mattermost team unavailable: {detail}'
            return result
        company_team_name = result.get('team_name', '')

        # Shared collaboration team — AI peers + cross-subscriber Town Square
        shared_team_id = _ensure_dev_team(mm_url, headers, result)
        if not shared_team_id:
            result['success'] = False
            detail = result.get('dev_team_error') or result.get('team_error') or 'unknown'
            result['error'] = f'Shared Mattermost team unavailable: {detail}'
            return result
        shared_team_name = _shared_team_name()

        # Ensure system admin user (mmadmin) exists and has system admin role
        system_admin_id = _ensure_system_admin_user(mm_url, headers, result)

        # Add system admin to shared team if both exist
        if system_admin_id and shared_team_id:
            _add_user_to_team(mm_url, headers, shared_team_id, system_admin_id, result)
            logger.info("[MM-PROV] Added system admin to shared team")

        user_id = _create_user(mm_url, headers, admin_email, username, effective_password, result)
        if not user_id:
            err_detail = result.get('user_error') or 'could not create or link Mattermost user'
            result['success'] = False
            result['error'] = f'Mattermost user unavailable: {err_detail}'
            if tenant_app_id:
                try:
                    from dose.models import TenantApp
                    ta = TenantApp.objects.filter(id=tenant_app_id).first()
                    if ta:
                        mark_tenant_app_error(ta, result['error'])
                except Exception:
                    pass
            logger.error("[MM-PROV] Failed for %s — no MM user: %s", tenant_schema, err_detail)
            return result

        token = ''
        _add_user_to_team(mm_url, headers, company_team_id, user_id, result)
        _add_user_to_team(mm_url, headers, shared_team_id, user_id, result)
        set_mattermost_shared_team_landing(mm_url, headers, user_id, shared_team_id, result)
        token = _create_user_token(mm_url, headers, user_id, result) or ''

        oidc_enabled = False
        if oauth_client_id and oauth_client_secret:
            oidc_enabled = _configure_oidc(mm_url, headers, oauth_client_id, oauth_client_secret, result)

        mm_username = result.get('mm_username') or username
        _store_credentials(
            tenant_app_id, mm_url, token, user_id,
            mm_username, result.get('mm_effective_password') or effective_password,
            company_team_id, company_team_name, oidc_enabled,
            shared_team_id=shared_team_id,
            shared_team_name=shared_team_name,
        )

        _send_welcome_email(admin_email, mm_url, display_name)

        result['success'] = True
        result['oidc_enabled'] = oidc_enabled
        result['message'] = 'Mattermost tenant provisioned (company + shared teams)'
        result['company_team_id'] = company_team_id
        result['company_team_name'] = company_team_name
        result['shared_team_id'] = shared_team_id
        result['shared_team_name'] = shared_team_name
        logger.info(
            "[MM-PROV] Success for %s (company=%s shared=%s user=%s)",
            tenant_schema, company_team_name, shared_team_name, user_id,
        )

        # ── Setup AI Agents in shared Town Square ────────────────────────────────
        try:
            from dose.services.mattermost_multi_agent_bot import MattermostMultiAgentBot
            bot = MattermostMultiAgentBot(mm_url, team_name=shared_team_name)
            bot.say_hello_all()
            result['ai_agents_setup'] = True
            logger.info("[MM-PROV] AI agents initialized in Town Square")
        except Exception as agent_exc:
            logger.warning("[MM-PROV] AI agent setup failed (non-fatal): %s", agent_exc)
            result['ai_agents_setup'] = False
            result['ai_agents_error'] = str(agent_exc)

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


def ensure_dual_mattermost_teams(
    tenant_schema: str,
    company_name: str = '',
) -> Dict[str, Any]:
    """
    Backfill dual-team membership for an existing tenant:
      - mm_team_id / mm_team_name  → private company team
      - mm_shared_team_id / mm_shared_team_name → shared collaboration team
    Ensures the MM user is a member of both teams.
    """
    result: Dict[str, Any] = {'tenant_schema': tenant_schema, 'success': False}
    admin_token = _get_admin_token()
    if not admin_token:
        result['error'] = 'MATTERMOST_ADMIN_TOKEN not configured'
        return result

    headers = {"Authorization": f"Bearer {admin_token}"}
    mm_url = _get_mattermost_base_url()
    shared_name = _shared_team_name()

    try:
        from django.db import connection
        from dose.models import Tenant, TenantApp

        tenant = Tenant.objects.filter(schema_name=tenant_schema).first()
        if not tenant:
            result['error'] = f'Tenant not found: {tenant_schema}'
            return result

        ta = TenantApp.public_bundles.filter(tenant=tenant, app_name='mattermost').first()
        if not ta:
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{tenant.schema_name}", public')
            ta = TenantApp.objects.filter(tenant=tenant, app_name='mattermost').first()
        if not ta:
            result['error'] = 'No Mattermost TenantApp'
            return result

        extra = dict(ta.extra_config or {})
        user_id = (extra.get('mm_user_id') or '').strip()
        if not user_id:
            result['error'] = 'mm_user_id missing in extra_config'
            return result

        shared_team_id = _ensure_dev_team(mm_url, headers, result)
        if not shared_team_id:
            result['error'] = result.get('dev_team_error') or 'shared team unavailable'
            return result

        _add_user_to_team(mm_url, headers, shared_team_id, user_id, result)
        set_mattermost_shared_team_landing(mm_url, headers, user_id, shared_team_id, result)

        existing_team_id = (extra.get('mm_team_id') or '').strip()
        existing_team_name = (extra.get('mm_team_name') or '').strip()
        company_team_id = ''
        company_team_name = ''

        if existing_team_id and existing_team_id != shared_team_id:
            company_team_id = existing_team_id
            company_team_name = existing_team_name
            _add_user_to_team(mm_url, headers, company_team_id, user_id, result)
        else:
            # Config only had shared team (or nothing) — infer private team from MM memberships
            try:
                teams_resp = requests.get(
                    f"{mm_url}/api/v4/users/{user_id}/teams",
                    headers=headers,
                    timeout=15,
                )
                if teams_resp.status_code == 200:
                    for team in teams_resp.json():
                        if team.get('id') and team.get('id') != shared_team_id:
                            company_team_id = team['id']
                            company_team_name = team.get('name') or ''
                            break
            except Exception as exc:
                logger.warning("[MM-PROV] Could not list user teams: %s", exc)

            if not company_team_id:
                display = company_name or tenant.name or tenant_schema
                prov_result: Dict[str, Any] = {}
                company_team_id = _create_team(
                    mm_url, headers, tenant_schema, display, prov_result,
                ) or ''
                company_team_name = prov_result.get('team_name') or ''
                if company_team_id:
                    _add_user_to_team(mm_url, headers, company_team_id, user_id, result)

        extra['mm_shared_team_id'] = shared_team_id
        extra['mm_shared_team_name'] = shared_name
        if company_team_id:
            extra['mm_team_id'] = company_team_id
        if company_team_name:
            extra['mm_team_name'] = company_team_name
        with connection.cursor() as cursor:
            cursor.execute('SET search_path TO public,pg_catalog')
        ta.extra_config = extra
        ta.save(update_fields=['extra_config'])

        result['success'] = True
        result['mm_user_id'] = user_id
        result['mm_team_name'] = company_team_name
        result['mm_team_id'] = company_team_id
        result['mm_shared_team_name'] = shared_name
        result['mm_shared_team_id'] = shared_team_id
        result['message'] = (
            f'Dual teams: company={company_team_name or "?"} shared={shared_name}'
        )
        logger.info(
            "[MM-PROV] Dual-team backfill %s company=%s shared=%s user=%s",
            tenant_schema, company_team_name, shared_name, user_id,
        )
        return result
    except Exception as exc:
        logger.error("[MM-PROV] Dual-team backfill failed for %s: %s", tenant_schema, exc, exc_info=True)
        result['error'] = str(exc)
        return result


def ensure_tenant_on_shared_mattermost_team(tenant_schema: str) -> Dict[str, Any]:
    """Legacy alias — use ensure_dual_mattermost_teams."""
    return ensure_dual_mattermost_teams(tenant_schema)
