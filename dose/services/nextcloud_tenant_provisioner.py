# atomic_services/nextcloud_tenant_provisioner.py
from typing import Dict, Any
from django.db import connection
from celery import shared_task
import logging
import requests
import secrets
import string
from dose.services.email_service import GmailEmailService
from dose.services.oauth2_registration import mark_tenant_app_active, mark_tenant_app_error

logger = logging.getLogger(__name__)

NEXTCLOUD_API_BASE = "https://nextcloud.polysaas.online/api/http.php"  # or internal service URL

OIDC_DISCOVERY = "https://polysaas.online/o/.well-known/openid-configuration"

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
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
    Atomic Service: Create Nextcloud tenant + admin user on new subscription
    Triggered when "Nextcloud" is checked on subscribe form
    """
    # 1. Generate secure password
    password = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(20))

    # 2. Create Nextcloud tenant (multi-tenant via separate DB schema or prefix)
    # Using Nextcloud's REST API + our internal provisioning endpoint
    create_tenant_payload = {
        "action": "create_tenant",
        "tenant_schema": tenant_schema,        # e.g. tenant_acme
        "company_name": company_name or tenant_name,
        "admin_email": admin_email,
        "admin_password": password,
        "plan": "professional"  # or map from PolySaaS tier
    }

    tenant_resp = requests.post(f"{NEXTCLOUD_API_BASE}/tenants", json=create_tenant_payload, timeout=30)
    tenant_resp.raise_for_status()
    nextcloud_url = tenant_resp.json()["tenant_url"]  # e.g. https://acme.nextcloud.polysaas.online

    # 3. Send welcome email via Gmail API
    try:
        email_svc = GmailEmailService(credentials_file='gmail_creds.json')
        welcome_subject = f"Welcome to PolySaaS + Nextcloud – Your File Storage is Ready"
        welcome_body = f"""
        <h2>Your PolySaaS tenant is live, and your Nextcloud is ready!</h2>

        <p><strong>File Storage URL:</strong> <a href="{nextcloud_url}">{nextcloud_url}</a></p>

        <p><strong>Login Credentials:</strong></p>
        <ul>
            <li><strong>Email:</strong> {admin_email}</li>
            <li><strong>Password:</strong> {password}</li>
        </ul>

        <p><em>⚠️ Important: Change this password immediately after first login!</em></p>

        <p>You can access your file storage anytime from your PolySaaS dashboard.</p>

        <p>Need help? Contact our support team.</p>

        <p>Welcome to PolySaaS!<br>
        The PolySaaS Team</p>
        """

        email_result = email_svc.send_email(
            to_email=admin_email,
            subject=welcome_subject,
            body=welcome_body
        )

        if email_result.get('success'):
            print(f"Welcome email sent to {admin_email} (Message ID: {email_result.get('message_id')})")
        else:
            print(f"Warning: Failed to send welcome email: {email_result.get('error')}")

    except Exception as e:
        print(f"Warning: Email service error: {str(e)}")
        # Continue with provisioning even if email fails

    # 4. Configure OIDC provider if credentials provided
    from dose.models import TenantApp
    tenant_app = None
    if tenant_app_id:
        try:
            tenant_app = TenantApp.objects.get(id=tenant_app_id)
        except TenantApp.DoesNotExist:
            pass

    if oauth_client_id and oauth_client_secret:
        try:
            # TODO: When Nextcloud Docker container is available, configure via occ:
            # docker_exec("occ app:enable user_oidc")
            # docker_exec(f"occ user_oidc:provider PolySaaS "
            #             f"--clientid='{oauth_client_id}' "
            #             f"--clientsecret='{oauth_client_secret}' "
            #             f"--discoveryuri='{OIDC_DISCOVERY}' "
            #             f"--scope='openid email profile' "
            #             f"--unique-uid=1 --check-bearer=1")
            logger.info("OAuth2 credentials ready for Nextcloud tenant %s (client_id=%s)", tenant_name, oauth_client_id)
        except Exception as e:
            logger.warning("Nextcloud OIDC config failed for %s: %s", tenant_name, e)

    if tenant_app:
        mark_tenant_app_active(tenant_app, app_url=nextcloud_url)

    return {
        "success": True,
        "nextcloud_url": nextcloud_url,
        "nextcloud_credentials": {
            "email": admin_email,
            "password": password,
            "note": "Auto-generated – force change on first login"
        },
        "sso": bool(oauth_client_id),
        "message": "Nextcloud tenant provisioned",
    }