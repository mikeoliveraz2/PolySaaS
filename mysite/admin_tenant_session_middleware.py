# DO NOT MODIFY: Critical system file. Ask before making changes.
# DO NOT MODIFY: Critical system file
import logging
from django.utils.deprecation import MiddlewareMixin
from dose.models import UserProfile

class AdminTenantSessionMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Keep tenant session keys aligned for authenticated users in the real Django admin.
        if request.path.startswith('/admin/') and request.user.is_authenticated:
            logger = logging.getLogger(__name__)
            try:
                tenant_id = request.session.get('tenant_id')
                profile = None
                tenant = None
                # Always use the tenant from the user's UserProfile
                from dose.models import Tenant
                profile = None
                tenant = None
                # Always use the tenant from the current schema for the user
                profile = UserProfile.objects.filter(user=request.user).first()
                if profile:
                    tenant = profile.tenant
                    tenant_id = tenant.id
                if profile and tenant:
                    request.session['tenant_id'] = tenant.id
                    request.session['tenant_name'] = tenant.name
                    request.session['tenant_slug'] = tenant.slug
                    request.session['tenant_description'] = getattr(tenant, 'description', '')
                    if hasattr(tenant, 'logo') and tenant.logo:
                        request.session['tenant_logo_url'] = tenant.logo.url
                    logger.info(f"AdminTenantSessionMiddleware: Set tenant session keys for admin user {request.user.username}: tenant_id={tenant.id}, tenant_name={tenant.name}")
                    request.session.save()
                else:
                    logger.warning(f"AdminTenantSessionMiddleware: No UserProfile found for admin user {request.user.username} and tenant_id={tenant_id}")
            except Exception as e:
                logger.error(f"AdminTenantSessionMiddleware: Error setting tenant session keys: {e}")
        return response
