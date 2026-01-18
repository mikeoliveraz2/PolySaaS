from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from dose.models import UserProfile

class AdminTenantSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        import logging
        logger = logging.getLogger(__name__)
        # Only read session data for admin panel and authenticated users
        if request.path.startswith('/admin-panel/') and request.user.is_authenticated:
            logger.info(f"AdminTenantSessionMiddleware: tenant_id in session for user {request.user.username}: {request.session.get('tenant_id')}")
        logger.debug(f"AdminTenantSessionMiddleware: session contents after process_request: {dict(request.session.items())}")
