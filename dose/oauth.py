"""
PolySaaS OAuth2/OIDC Provider — Tenant-Aware Validator & Helpers

Extends django-oauth-toolkit to inject tenant claims into OIDC ID tokens,
so downstream apps (Mattermost, Odoo, Nextcloud) know which tenant a user
belongs to without a second lookup.
"""
import logging

from oauth2_provider.oauth2_validators import OAuth2Validator

logger = logging.getLogger(__name__)


class TenantAwareValidator(OAuth2Validator):
    """Custom OAuth2 validator that includes tenant info in OIDC claims."""

    oidc_claim_scope = OAuth2Validator.oidc_claim_scope
    oidc_claim_scope.update({
        'tenant_id': 'tenant',
        'tenant_name': 'tenant',
        'tenant_slug': 'tenant',
    })

    def get_additional_claims(self, request):
        """Include tenant information in OIDC ID tokens and UserInfo responses."""
        user = request.user
        claims = {}

        try:
            profile = getattr(user, 'userprofile', None)
            if profile and profile.tenant_id:
                claims['tenant_id'] = profile.tenant_id
                claims['tenant_name'] = profile.tenant.name
                claims['tenant_slug'] = profile.tenant.slug
        except Exception:
            logger.warning("Could not resolve tenant for user %s", user.pk)

        return claims

    def get_userinfo_claims(self, request):
        """Extend the standard UserInfo response with tenant data."""
        claims = super().get_userinfo_claims(request)
        claims.update(self.get_additional_claims(request))
        return claims


def get_redirect_uri(app_name, tenant_schema):
    """Return the expected OAuth2 redirect URI for a given app type."""
    base_urls = {
        'mattermost': 'https://mm.polysaas.online',
        'odoo': 'https://odoo.polysaas.online',
        'nextcloud': 'https://nextcloud.polysaas.online',
    }
    redirect_paths = {
        'mattermost': '/signup/openid/complete',
        'odoo': '/auth_oauth/signin',
        'nextcloud': '/apps/user_oidc/code',
    }
    base = base_urls.get(app_name, '')
    path = redirect_paths.get(app_name, '/callback')
    return f"{base}{path}"
