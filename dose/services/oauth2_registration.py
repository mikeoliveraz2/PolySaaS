"""
Shared helper for registering OAuth2 applications in django-oauth-toolkit
and creating the corresponding TenantApp record.

Called from subscription_views.py during tenant provisioning. Each bundled
app gets its own OAuth2 Application (Client ID + Secret) scoped to the tenant.

When django-oauth-toolkit (oauth2_provider) is not installed, this module
still loads; register_oauth2_app_for_tenant will raise if called.
mark_tenant_app_active and mark_tenant_app_error do not require oauth2_provider.
"""
import logging

from django.apps import apps

try:
    from oauth2_provider.models import Application
except ImportError:
    Application = None

from dose.models import Tenant, TenantApp
from dose.oauth import get_redirect_uri

logger = logging.getLogger(__name__)


def register_oauth2_app_for_tenant(tenant_id, app_name, user):
    """
    Register an OAuth2 Application in DOT for a tenant+app pair.

    Returns (client_id, client_secret, tenant_app) or raises on failure.
    Requires django-oauth-toolkit (oauth2_provider) to be installed.
    """
    if Application is None:
        raise RuntimeError(
            "django-oauth-toolkit is not installed; install it to use OAuth2 app registration."
        )

    tenant = Tenant.objects.get(id=tenant_id)

    redirect_uri = get_redirect_uri(app_name, tenant.schema_name)

    oauth_app = Application.objects.create(
        name=f"{tenant.name}-{app_name}",
        user=user,
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris=redirect_uri,
        algorithm='RS256',
    )

    defaults = {'status': 'provisioning'}
    if apps.is_installed('oauth2_provider'):
        defaults['oauth_application'] = oauth_app

    tenant_app, _ = TenantApp.objects.update_or_create(
        tenant=tenant,
        app_name=app_name,
        defaults=defaults,
    )

    logger.info(
        "Registered OAuth2 app: tenant=%s app=%s client_id=%s",
        tenant.name, app_name, oauth_app.client_id,
    )

    return oauth_app.client_id, oauth_app.client_secret, tenant_app


def mark_tenant_app_active(tenant_app, app_url=''):
    """Mark a TenantApp as successfully provisioned."""
    tenant_app.status = 'active'
    if app_url:
        tenant_app.app_url = app_url
    tenant_app.save(update_fields=['status', 'app_url'])


def mark_tenant_app_error(tenant_app, error_msg):
    """Mark a TenantApp as failed with an error message."""
    tenant_app.status = 'error'
    tenant_app.last_error = str(error_msg)[:2000]
    tenant_app.save(update_fields=['status', 'last_error'])
