# atomic_services/nextcloud_tenant_provisioner.py
from typing import Dict, Any
from django.db import connection
from celery import shared_task
import requests
import secrets
import string
from dose.services.email_service import GmailEmailService

NEXTCLOUD_API_BASE = "https://nextcloud.polysaas.online/api/http.php"  # or internal service URL

@shared_task
def provision_nextcloud_tenant(tenant_schema: str, tenant_name: str, admin_email: str, company_name: str) -> Dict[str, Any]:
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

    return {
        "success": True,
        "nextcloud_url": nextcloud_url,
        "nextcloud_credentials": {
            "email": admin_email,
            "password": password,
            "note": "Auto-generated – force change on first login"
        },
        "message": "Nextcloud tenant provisioned instantly"
    }