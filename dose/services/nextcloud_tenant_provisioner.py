# dose/services/nextcloud_tenant_provisioner.py
"""
Nextcloud Tenant Provisioner — creates a user in the shared Nextcloud instance
for a new PolySaaS tenant subscription.

Architecture:
  • A single shared Nextcloud instance serves all tenants.
  • Each new tenant gets a user account provisioned via Nextcloud OCS API.
  • Nextcloud URL and admin credentials come from Django settings (env vars).
  • The provisioner also creates a PassThroughEndpoint in the tenant schema
    so the sidebar "NextCloud" link appears immediately.

Settings used:
  NEXTCLOUD_SHARED_URL            — e.g. http://polysaas-nextcloud:80
  NEXTCLOUD_SHARED_ADMIN_LOGIN    — e.g. ncadmin
  POLYSAAS_APP_ADMIN_PASSWORD     — shared admin password (e.g. PolySaaS2026!)
"""
from typing import Dict, Any
import logging

import requests as http_requests

from django.conf import settings
from django.db import connection

from celery import shared_task

from dose.models import TenantApp, PassThroughEndpoint
from dose.services.oauth2_registration import mark_tenant_app_active, mark_tenant_app_error

logger = logging.getLogger(__name__)


def _get_nextcloud_shared_config() -> Dict[str, str]:
    """Return connection config for the shared Nextcloud instance."""
    return {
        'url': getattr(settings, 'NEXTCLOUD_SHARED_URL', 'https://polysaas-nextcloud.onrender.com'),
        'admin_login': getattr(settings, 'NEXTCLOUD_SHARED_ADMIN_LOGIN', 'ncadmin'),
        'admin_password': getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!'),
    }


def _nextcloud_create_user(config: Dict[str, str], *, userid: str, display_name: str, password: str, email: str) -> Dict[str, Any]:
    """
    Create a user in Nextcloud via OCS Provisioning API.
    If user already exists, returns success with a note.

    Nextcloud OCS docs: https://docs.nextcloud.com/server/latest/admin_manual/configuration_user/user_provisioning_api.html
    """
    url = config['url'].rstrip('/')
    admin_login = config['admin_login']
    admin_password = config['admin_password']

    # OCS endpoint for user creation
    ocs_url = f"{url}/ocs/v1.php/cloud/users"

    payload = {
        'userid': userid,
        'displayName': display_name,
        'password': password,
        'email': email,
    }

    try:
        resp = http_requests.post(
            ocs_url,
            data=payload,
            auth=(admin_login, admin_password),
            headers={'OCS-APIRequest': 'true'},
            timeout=30,
        )

        # OCS API returns XML by default; check status code
        if resp.status_code == 200:
            # Check OCS status in response (100 = success, 102 = user exists)
            if '<statuscode>100</statuscode>' in resp.text:
                logger.info("[NextcloudProvisioner] Created user '%s'", userid)
                return {'ok': True, 'status': 'created', 'userid': userid}
            elif '<statuscode>102</statuscode>' in resp.text:
                logger.info("[NextcloudProvisioner] User '%s' already exists", userid)
                return {'ok': True, 'status': 'already_exists', 'userid': userid}
            else:
                logger.warning("[NextcloudProvisioner] OCS response: %s", resp.text[:300])
                return {'ok': False, 'status': 'ocs_error', 'response': resp.text[:300]}
        else:
            logger.warning("[NextcloudProvisioner] HTTP %d: %s", resp.status_code, resp.text[:200])
            return {'ok': False, 'status': 'http_error', 'status_code': resp.status_code}

    except Exception as exc:
        logger.error("[NextcloudProvisioner] Request failed: %s", exc)
        return {'ok': False, 'status': 'connection_error', 'error': str(exc)}


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def provision_nextcloud_tenant(
    self,
    tenant_schema: str,
    tenant_name: str,
    admin_email: str,
    company_name: str,
    oauth_client_id: str = '',
    oauth_client_secret: str = '',
    tenant_app_id: int = None,
) -> Dict[str, Any]:
    """
    Celery task: provision a Nextcloud user for a new PolySaaS tenant.

    Steps:
      1. Create PassThroughEndpoint in tenant schema (sidebar link)
      2. Create user in shared Nextcloud via OCS API
      3. Update TenantApp.extra_config with credentials
      4. Mark TenantApp as 'active'
      5. (Optional) Send welcome email
    """
    config = _get_nextcloud_shared_config()
    nextcloud_url = config['url']
    password = config['admin_password']

    # Resolve TenantApp record
    tenant_app = None
    if tenant_app_id:
        try:
            tenant_app = TenantApp.objects.get(id=tenant_app_id)
        except TenantApp.DoesNotExist:
            logger.warning("[NextcloudProvisioner] TenantApp id=%s not found", tenant_app_id)

    # ── Step 1: Create PassThroughEndpoint ────────────────────────────────
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{tenant_schema}", public')
        PassThroughEndpoint.objects.update_or_create(
            trigger_path='nextcloud',
            defaults={
                'endpoint_url': nextcloud_url,
                'description': f'NextCloud File Storage for {company_name or tenant_name}',
                'is_enabled': True,
                'passthrough_type': 'scraper',
                'integration_mode': 'web_api',
                'api_endpoint': f"{nextcloud_url}/ocs/v1.php",
                'show_in_menu': True,
                'menu_title': 'NextCloud',
                'menu_icon': 'cloud',
                'menu_sort_order': 30,
                'starting_uri': '/index.php/login',
            }
        )
        logger.info("[NextcloudProvisioner] PassThroughEndpoint for '%s' ensured", tenant_schema)
    except Exception as e:
        logger.warning("[NextcloudProvisioner] PassThroughEndpoint creation failed: %s", e)

    # ── Step 2: Create Nextcloud user via OCS API ─────────────────────────
    # Use a short userid derived from email (before @)
    userid = admin_email.split('@')[0] if '@' in admin_email else admin_email
    display_name = company_name or tenant_name

    result = _nextcloud_create_user(
        config,
        userid=userid,
        display_name=display_name,
        password=password,
        email=admin_email,
    )

    if not result.get('ok'):
        err_msg = result.get('error') or result.get('response') or 'unknown error'
        logger.error("[NextcloudProvisioner] User creation failed for %s: %s", tenant_name, err_msg)
        if tenant_app:
            mark_tenant_app_error(tenant_app, err_msg)
        raise self.retry(exc=RuntimeError(err_msg))

    # ── Step 3: Update TenantApp.extra_config ─────────────────────────────
    if tenant_app:
        try:
            extra = tenant_app.extra_config if isinstance(tenant_app.extra_config, dict) else {}
            extra.update({
                'nc_login': userid,
                'nc_password': password,
                'nc_email': admin_email,
                'nc_url': nextcloud_url,
                'nc_userid': userid,
            })
            tenant_app.extra_config = extra
            tenant_app.save(update_fields=['extra_config'])
        except Exception as e:
            logger.warning("[NextcloudProvisioner] Failed to update TenantApp.extra_config: %s", e)

    # ── Step 4: Mark active ───────────────────────────────────────────────
    if tenant_app:
        mark_tenant_app_active(tenant_app, app_url=nextcloud_url)

    # ── Step 5: Welcome email (best-effort) ───────────────────────────────
    try:
        from dose.services.email_service import GmailEmailService
        email_svc = GmailEmailService(credentials_file='gmail_creds.json')
        email_svc.send_email(
            to_email=admin_email,
            subject="Welcome to PolySaaS + NextCloud – Your File Storage is Ready",
            body=f"""
            <h2>Your NextCloud file storage is ready!</h2>
            <p><strong>URL:</strong> Access NextCloud from your PolySaaS dashboard sidebar.</p>
            <p><strong>Username:</strong> {userid}</p>
            <p><strong>Password:</strong> {password}</p>
            <p><em>⚠️ Change this password after first login.</em></p>
            <p>Welcome to PolySaaS!<br>The PolySaaS Team</p>
            """,
        )
        logger.info("[NextcloudProvisioner] Welcome email sent to %s", admin_email)
    except Exception as e:
        logger.warning("[NextcloudProvisioner] Welcome email failed (non-fatal): %s", e)

    logger.info(
        "[NextcloudProvisioner] Provisioning complete: tenant=%s userid=%s",
        tenant_name, userid,
    )

    return {
        "success": True,
        "nextcloud_url": nextcloud_url,
        "nextcloud_userid": userid,
        "nextcloud_credentials": {
            "userid": userid,
            "password": password,
            "email": admin_email,
        },
        "sso": bool(oauth_client_id),
        "message": f"Nextcloud user '{userid}' provisioned in shared instance",
    }