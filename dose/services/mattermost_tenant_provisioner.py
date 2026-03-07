"""
Atomic Service: Provision Mattermost team + configure OIDC SSO for a new tenant.

Creates a Mattermost team, configures OpenID Connect to point at the
PolySaaS OIDC provider, and sends a welcome email with SSO instructions
(no password — user logs in via PolySaaS).
"""
from typing import Dict, Any
from celery import shared_task
import logging
import requests

from dose.services.email_service import GmailEmailService
from dose.services.oauth2_registration import mark_tenant_app_active, mark_tenant_app_error

logger = logging.getLogger(__name__)

MATTERMOST_URL = "https://mm.polysaas.online"
MATTERMOST_ADMIN_TOKEN_ENV = "MATTERMOST_ADMIN_TOKEN"

OIDC_DISCOVERY = "https://polysaas.online/o/.well-known/openid-configuration"


def _get_admin_token():
    """Retrieve Mattermost admin personal access token from env or settings."""
    import os
    token = os.environ.get(MATTERMOST_ADMIN_TOKEN_ENV, '')
    if not token:
        from django.conf import settings
        token = getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '')
    return token


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def provision_mattermost_tenant(
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
    Provision a Mattermost team with OIDC SSO for the tenant.

    Steps:
      1. Create a Mattermost team for the tenant
      2. Configure OIDC (OpenIdSettings) via /api/v4/config
      3. Send welcome email (SSO-based, no password)
    """
    from dose.models import TenantApp

    tenant_app = None
    if tenant_app_id:
        try:
            tenant_app = TenantApp.objects.get(id=tenant_app_id)
        except TenantApp.DoesNotExist:
            pass

    admin_token = _get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}"}
    mm_url = MATTERMOST_URL

    try:
        # 1. Create team
        team_resp = requests.post(
            f"{mm_url}/api/v4/teams",
            headers=headers,
            json={
                "name": tenant_schema[:64].lower(),
                "display_name": company_name or tenant_name,
                "type": "I",  # Invite-only
            },
            timeout=30,
        )
        if team_resp.status_code == 201:
            team = team_resp.json()
            logger.info("Created Mattermost team: %s (id=%s)", team['name'], team['id'])
        elif team_resp.status_code == 400 and 'already exists' in team_resp.text.lower():
            logger.info("Mattermost team %s already exists, continuing", tenant_schema)
        else:
            team_resp.raise_for_status()

        # 2. Configure OIDC if credentials provided
        if oauth_client_id and oauth_client_secret:
            oidc_resp = requests.patch(
                f"{mm_url}/api/v4/config",
                headers=headers,
                json={
                    "OpenIdSettings": {
                        "Enable": True,
                        "Secret": oauth_client_secret,
                        "Id": oauth_client_id,
                        "DiscoveryEndpoint": OIDC_DISCOVERY,
                        "ButtonText": "Log in with PolySaaS",
                        "ButtonColor": "#003399",
                    }
                },
                timeout=30,
            )
            if oidc_resp.status_code == 200:
                logger.info("Configured OIDC on Mattermost for tenant %s", tenant_name)
            else:
                logger.warning(
                    "OIDC config returned %s: %s", oidc_resp.status_code, oidc_resp.text[:200]
                )

        # 3. Send welcome email (SSO — no password)
        try:
            email_svc = GmailEmailService(credentials_file='gmail_creds.json')
            welcome_body = f"""
            <h2>Your PolySaaS tenant is live, and Mattermost is ready!</h2>

            <p><strong>Chat URL:</strong> <a href="{mm_url}">{mm_url}</a></p>

            <p><strong>How to log in:</strong> Click "Log in with PolySaaS" on the Mattermost login page.
            You'll be signed in automatically with your PolySaaS account — no separate password needed.</p>

            <p>Your team (<strong>{company_name or tenant_name}</strong>) is already set up and waiting for you.</p>

            <p>Need help? Contact our support team.</p>

            <p>Welcome to PolySaaS!<br>The PolySaaS Team</p>
            """
            email_svc.send_email(
                to_email=admin_email,
                subject="Welcome to PolySaaS + Mattermost - Your Team Chat is Ready",
                body=welcome_body,
            )
        except Exception as e:
            logger.warning("Mattermost welcome email failed: %s", e)

        if tenant_app:
            mark_tenant_app_active(tenant_app, app_url=mm_url)

        return {
            "success": True,
            "mattermost_url": mm_url,
            "team": tenant_schema,
            "sso": bool(oauth_client_id),
            "message": "Mattermost tenant provisioned with SSO",
        }

    except requests.exceptions.HTTPError as exc:
        if tenant_app:
            mark_tenant_app_error(tenant_app, str(exc))
        if exc.response is not None and exc.response.status_code >= 500:
            raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))
        raise

    except Exception as exc:
        if tenant_app:
            mark_tenant_app_error(tenant_app, str(exc))
        logger.error("Mattermost provisioning failed for %s: %s", tenant_schema, exc)
        raise
