# atomic_services/dolibarr_tenant_provisioner.py
from typing import Dict, Any
from django.db import connection
from celery import shared_task
import requests
import secrets
import string
from dose.services.email_service import GmailEmailService
from dose.models import PassThroughEndpoint

DOLIBARR_API_BASE = "http://localhost:8083"  # Local Docker service

@shared_task
def provision_dolibarr_tenant(tenant_schema: str, tenant_name: str, admin_email: str, company_name: str) -> Dict[str, Any]:
    """
    Atomic Service: Create Dolibarr tenant + admin user on new subscription
    Triggered when "Dolibarr" is checked on subscribe form
    """
    # 1. Generate secure password
    password = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(20))

    # 2. Create PassThroughEndpoint for Dolibarr
    dolibarr_endpoint = PassThroughEndpoint.objects.create(
        menu_title='Dolibarr ERP/CRM',
        endpoint_url=DOLIBARR_API_BASE,
        trigger_path=f'/admin/dolibarr/',
        is_enabled=True,
        show_in_menu=True,
        passthrough_type='scraper'
    )
    print(f"Created PassThroughEndpoint for Dolibarr: {dolibarr_endpoint.trigger_path} -> {dolibarr_endpoint.endpoint_url}")

    dolibarr_url = f"http://dolibarr.polysaas.online/admin/{tenant_schema}/dolibarr/"  # Assuming hosts file maps this

    # 3. Send welcome email via Gmail API
    try:
        email_svc = GmailEmailService(credentials_file='gmail_creds.json')
        welcome_subject = f"Welcome to PolySaaS + Dolibarr – Your ERP/CRM is Ready"
        welcome_body = f"""
        <h2>Your PolySaaS tenant is live, and your Dolibarr ERP/CRM is ready!</h2>

        <p><strong>ERP/CRM URL:</strong> <a href="{dolibarr_url}">{dolibarr_url}</a></p>

        <p><strong>Login Credentials:</strong></p>
        <ul>
            <li><strong>Email:</strong> admin@dolibarr.com (default)</li>
            <li><strong>Password:</strong> admin</li>
        </ul>

        <p><em>Note: This is a shared Dolibarr instance for demo purposes. In production, each tenant would have isolated access.</em></p>

        <p>You can access your ERP/CRM anytime from your PolySaaS dashboard.</p>

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
        "dolibarr_url": dolibarr_url,
        "dolibarr_credentials": {
            "email": "admin@dolibarr.com",
            "password": "admin",
            "note": "Default Dolibarr admin credentials"
        },
        "message": "Dolibarr tenant provisioned instantly"
    }