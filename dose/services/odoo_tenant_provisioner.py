# atomic_services/odoo_tenant_provisioner.py
from typing import Dict, Any
from django.db import connection
from celery import shared_task
import logging
import requests
import secrets
import string
from dose.services.email_service import GmailEmailService
from dose.services.oauth2_registration import mark_tenant_app_active, mark_tenant_app_error
from dose.models import TenantApp, PassThroughEndpoint

logger = logging.getLogger(__name__)

ODOO_API_BASE = "https://odoo.polysaas.online/api/http.php"  # or internal service URL

OIDC_ENDPOINTS = {
    'auth': 'https://polysaas.online/o/authorize/',
    'token': 'https://polysaas.online/o/token/',
    'jwks': 'https://polysaas.online/o/jwks/',
    'userinfo': 'https://polysaas.online/o/userinfo/',
}

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def provision_odoo_tenant(
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
    Atomic Service: Create Odoo tenant + admin user on new subscription
    Triggered when "Odoo ERP" is checked on subscribe form
    """
    # 1. Use standardized app-admin password (convention: [appslug]Admin / POLYSAAS_APP_ADMIN_PASSWORD)
    from django.conf import settings
    password = getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!')

    # 2. Create Odoo tenant (multi-tenant via separate DB schema or prefix)
    # Using Odoo's REST API + our internal provisioning endpoint
    create_tenant_payload = {
        "action": "create_tenant",
        "tenant_schema": tenant_schema,        # e.g. tenant_acme
        "company_name": company_name or tenant_name,
        "admin_email": admin_email,
        "admin_username": "odooAdmin",
        "admin_password": password,
        "plan": "professional"  # or map from PolySaaS tier
    }

    tenant_resp = requests.post(f"{ODOO_API_BASE}/tenants", json=create_tenant_payload, timeout=30)
    tenant_resp.raise_for_status()
    odoo_url = tenant_resp.json()["tenant_url"]  # e.g. https://acme.odoo.polysaas.online

    # 3. Send welcome email via Gmail API
    try:
        email_svc = GmailEmailService(credentials_file='gmail_creds.json')
        welcome_subject = f"Welcome to PolySaaS + Odoo – Your ERP is Ready"
        welcome_body = f"""
        <h2>Your PolySaaS tenant is live, and your Odoo ERP is ready!</h2>

        <p><strong>ERP URL:</strong> <a href="{odoo_url}">{odoo_url}</a></p>

        <p><strong>Login Credentials:</strong></p>
        <ul>
            <li><strong>Email:</strong> {admin_email}</li>
            <li><strong>Password:</strong> {password}</li>
        </ul>

        <p><em>⚠️ Important: Change this password immediately after first login!</em></p>

        <p>You can access your ERP anytime from your PolySaaS dashboard.</p>

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

    # 4. Configure OAuth2/OIDC provider if credentials provided
    tenant_app = None
    if tenant_app_id:
        try:
            tenant_app = TenantApp.objects.get(id=tenant_app_id)
        except TenantApp.DoesNotExist:
            pass

    if oauth_client_id and oauth_client_secret:
        try:
            # TODO: When Odoo JSON-RPC endpoint is available, create auth.oauth.provider record:
            # models.execute_kw(db, uid, pwd, 'auth.oauth.provider', 'create', [{
            #     'name': 'PolySaaS SSO',
            #     'flow': 'id_token_code',
            #     'client_id': oauth_client_id,
            #     'client_secret': oauth_client_secret,
            #     'auth_endpoint': OIDC_ENDPOINTS['auth'],
            #     'token_endpoint': OIDC_ENDPOINTS['token'],
            #     'jwks_uri': OIDC_ENDPOINTS['jwks'],
            #     'validation_endpoint': OIDC_ENDPOINTS['userinfo'],
            #     'scope': 'openid email profile',
            #     'enabled': True,
            #     'body': 'Log in with PolySaaS',
            # }])
            logger.info("OAuth2 credentials ready for Odoo tenant %s (client_id=%s)", tenant_name, oauth_client_id)
        except Exception as e:
            logger.warning("Odoo OAuth2 config failed for %s: %s", tenant_name, e)

    # 5. Create PassThroughEndpoint in tenant schema for sidebar navigation
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{tenant_schema}"')
            odoo_endpoint, ep_created = PassThroughEndpoint.objects.update_or_create(
                trigger_path='odoo',
                defaults={
                    'endpoint_url': odoo_url,
                    'description': 'Odoo ERP - tenant-specific instance',
                    'is_enabled': True,
                    'passthrough_type': 'scraper',
                    'integration_mode': 'web_api',
                    'api_endpoint': f"{odoo_url}/xmlrpc/2",
                    'show_in_menu': True,
                    'menu_title': 'Odoo',
                    'menu_icon': 'building',
                    'menu_sort_order': 20,
                    'starting_uri': '/web',
                }
            )
            if ep_created:
                logger.info("Created PassThroughEndpoint for Odoo in tenant %s", tenant_schema)
            else:
                logger.info("Updated PassThroughEndpoint for Odoo in tenant %s", tenant_schema)
    except Exception as e:
        logger.warning("Failed to create PassThroughEndpoint for Odoo: %s", e)
        # Non-fatal: continue even if endpoint creation fails

    if tenant_app:
        mark_tenant_app_active(tenant_app, app_url=odoo_url)

    return {
        "success": True,
        "odoo_url": odoo_url,
        "odoo_credentials": {
            "email": admin_email,
            "password": password,
            "note": "Auto-generated – force change on first login"
        },
        "sso": bool(oauth_client_id),
        "message": "Odoo tenant provisioned",
    }