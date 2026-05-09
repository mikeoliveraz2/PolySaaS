# dose/services/odoo_tenant_provisioner.py
"""
Odoo Tenant Provisioner — creates a user in the shared Odoo instance for a
new PolySaaS tenant subscription.

Architecture:
  • A single shared Odoo instance serves all tenants (multi-company model).
  • Each new tenant gets a `res.users` record with a `res.company` in Odoo.
  • Communication is via XML-RPC (same as OdooCustomerSyncService).
  • Odoo URL and admin credentials come from Django settings (env vars).
  • The provisioner also creates a PassThroughEndpoint in the tenant schema
    so the sidebar "Odoo" link appears immediately.

Settings used:
  ODOO_SHARED_URL              — e.g. https://polysaas-odoo2.onrender.com
  ODOO_SHARED_DB               — e.g. odoodb
  ODOO_SHARED_ADMIN_LOGIN      — e.g. odooAdmin
  POLYSAAS_APP_ADMIN_PASSWORD  — shared admin password (e.g. PolySaaS2026!)
"""
from typing import Dict, Any
import logging
import xmlrpc.client

from django.conf import settings
from django.db import connection, transaction

from celery import shared_task

from dose.models import TenantApp, PassThroughEndpoint
from dose.services.oauth2_registration import mark_tenant_app_active, mark_tenant_app_error

logger = logging.getLogger(__name__)


def _get_odoo_shared_config() -> Dict[str, str]:
    """Return connection config for the shared Odoo instance."""
    return {
        'url': getattr(settings, 'ODOO_SHARED_URL', 'https://polysaas-odoo2.onrender.com'),
        'db': getattr(settings, 'ODOO_SHARED_DB', 'odoodb'),
        'admin_login': getattr(settings, 'ODOO_SHARED_ADMIN_LOGIN', 'odooAdmin'),
        'admin_password': getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!'),
    }


def _odoo_authenticate(config: Dict[str, str]) -> int:
    """Authenticate to Odoo as admin via XML-RPC. Returns uid or raises."""
    common = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(config['db'], config['admin_login'], config['admin_password'], {})
    if not uid:
        raise RuntimeError(
            f"Odoo XML-RPC auth failed: url={config['url']} db={config['db']} login={config['admin_login']}"
        )
    return uid


def _odoo_create_user(config: Dict[str, str], uid: int, *, login: str, name: str, password: str) -> int:
    """
    Create a res.users record in Odoo for the new tenant admin.
    If the user already exists (same login), returns the existing user id.
    """
    models = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/object", allow_none=True)
    db = config['db']
    admin_pw = config['admin_password']

    # Check if user already exists
    existing = models.execute_kw(
        db, uid, admin_pw, 'res.users', 'search',
        [[['login', '=', login]]]
    )
    if existing:
        logger.info("[OdooProvisioner] User '%s' already exists (id=%d), skipping create", login, existing[0])
        return existing[0]

    # Resolve group IDs for the new user:
    #   base.group_user          → Internal User (basic access)
    #   account.group_account_invoice → Invoicing (Show full accounting features)
    # We look them up by XML ID so it works across Odoo versions.
    group_ids = []
    for xml_id in ['base.group_user', 'account.group_account_invoice', 'account.group_account_user']:
        try:
            module, name_part = xml_id.split('.')
            found = models.execute_kw(
                db, uid, admin_pw, 'ir.model.data', 'search_read',
                [[['module', '=', module], ['name', '=', name_part]]],
                {'fields': ['res_id'], 'limit': 1}
            )
            if found:
                group_ids.append((4, found[0]['res_id']))
        except Exception:
            pass
    if not group_ids:
        group_ids = [(4, 1)]  # Fallback: at minimum add base internal user

    vals = {
        'name': name,
        'login': login,
        'email': login,
        'password': password,
        'groups_id': group_ids,
    }
    new_uid = models.execute_kw(db, uid, admin_pw, 'res.users', 'create', [vals])
    logger.info("[OdooProvisioner] Created Odoo user '%s' (id=%d)", login, new_uid)

    # Set home action to Apps page (id=39) — avoids Discuss which crashes through proxy
    try:
        models.execute_kw(db, uid, admin_pw, 'res.users', 'write', [[new_uid], {'action_id': 39}])
    except Exception:
        pass

    return new_uid


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
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
    Celery task: provision an Odoo user for a new PolySaaS tenant.

    Steps:
      1. Create PassThroughEndpoint in tenant schema (sidebar link)
      2. Create res.users in shared Odoo via XML-RPC
      3. Update TenantApp.extra_config with final credentials
      4. Mark TenantApp as 'active'
      5. (Optional) Send welcome email
    """
    config = _get_odoo_shared_config()
    odoo_url = config['url']
    password = config['admin_password']

    # Resolve TenantApp record
    tenant_app = None
    if tenant_app_id:
        try:
            tenant_app = TenantApp.objects.get(id=tenant_app_id)
        except TenantApp.DoesNotExist:
            logger.warning("[OdooProvisioner] TenantApp id=%s not found", tenant_app_id)

    # ── Step 1: Create PassThroughEndpoint ────────────────────────────────
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{tenant_schema}", public')
        PassThroughEndpoint.objects.update_or_create(
            trigger_path='odoo',
            defaults={
                'endpoint_url': odoo_url,
                'description': f'Odoo ERP for {company_name or tenant_name}',
                'is_enabled': True,
                'passthrough_type': 'scraper',
                'integration_mode': 'web_api',
                'api_endpoint': f"{odoo_url}/web",
                'show_in_menu': True,
                'menu_title': 'Odoo',
                'menu_icon': 'building',
                'menu_sort_order': 20,
                'starting_uri': '/web',
            }
        )
        logger.info("[OdooProvisioner] PassThroughEndpoint for '%s' ensured", tenant_schema)
    except Exception as e:
        logger.warning("[OdooProvisioner] PassThroughEndpoint creation failed: %s", e)

    # ── Step 2: Create Odoo user via XML-RPC ──────────────────────────────
    try:
        uid = _odoo_authenticate(config)
        odoo_user_id = _odoo_create_user(
            config, uid,
            login=admin_email,
            name=company_name or tenant_name,
            password=password,
        )
    except Exception as exc:
        logger.error("[OdooProvisioner] Odoo user creation failed for %s: %s", tenant_name, exc)
        if tenant_app:
            mark_tenant_app_error(tenant_app, str(exc))
        # Retry via Celery
        raise self.retry(exc=exc)

    # ── Step 3: Update TenantApp.extra_config ─────────────────────────────
    if tenant_app:
        try:
            extra = tenant_app.extra_config if isinstance(tenant_app.extra_config, dict) else {}
            extra.update({
                'odoo_login': admin_email,
                'odoo_password': password,
                'odoo_db': config['db'],
                'odoo_user_id': odoo_user_id,
                'odoo_url': odoo_url,
            })
            tenant_app.extra_config = extra
            tenant_app.save(update_fields=['extra_config'])
        except Exception as e:
            logger.warning("[OdooProvisioner] Failed to update TenantApp.extra_config: %s", e)

    # ── Step 4: Mark active ───────────────────────────────────────────────
    if tenant_app:
        mark_tenant_app_active(tenant_app, app_url=odoo_url)

    # ── Step 5: Welcome email (best-effort) ───────────────────────────────
    try:
        from dose.services.email_service import GmailEmailService
        email_svc = GmailEmailService(credentials_file='gmail_creds.json')
        email_svc.send_email(
            to_email=admin_email,
            subject="Welcome to PolySaaS + Odoo – Your ERP Access is Ready",
            body=f"""
            <h2>Your Odoo ERP access is ready!</h2>
            <p><strong>URL:</strong> Access Odoo from your PolySaaS dashboard sidebar.</p>
            <p><strong>Login:</strong> {admin_email}</p>
            <p><strong>Password:</strong> {password}</p>
            <p><em>⚠️ Change this password after first login.</em></p>
            <p>Welcome to PolySaaS!<br>The PolySaaS Team</p>
            """,
        )
        logger.info("[OdooProvisioner] Welcome email sent to %s", admin_email)
    except Exception as e:
        logger.warning("[OdooProvisioner] Welcome email failed (non-fatal): %s", e)

    logger.info(
        "[OdooProvisioner] ✅ Provisioning complete: tenant=%s login=%s odoo_uid=%d",
        tenant_name, admin_email, odoo_user_id,
    )

    return {
        "success": True,
        "odoo_url": odoo_url,
        "odoo_user_id": odoo_user_id,
        "odoo_credentials": {
            "login": admin_email,
            "password": password,
            "db": config['db'],
        },
        "sso": bool(oauth_client_id),
        "message": f"Odoo user '{admin_email}' provisioned in shared instance",
    }