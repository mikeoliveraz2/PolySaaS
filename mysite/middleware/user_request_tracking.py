"""
User Request Tracking Middleware
Automatically records user request paths for dashboard display
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from dose.models.user_request_tracker import UserRequestTracker

logger = logging.getLogger(__name__)


class UserRequestTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically track user request paths
    Records paths for authenticated users to display in dashboard
    """

    # Paths to exclude from tracking (too noisy or not useful)
    EXCLUDE_PATHS = {
        '/admin/jsi18n/',
        '/static/',
        '/media/',
        '/favicon.ico',
        '/admin/select-theme/',
        '/admin/theme-selector/',
    }

    # Path prefixes to exclude
    EXCLUDE_PREFIXES = (
        '/static/',
        '/media/',
        '/admin/jsi18n',
        '/admin/__debug__',
    )

    def process_request(self, request):
        """
        Record the request path for authenticated users
        """
        try:
            # Skip if user not authenticated
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return None

            # Skip excluded paths
            if self._should_exclude_path(request.path):
                return None

            # Skip AJAX requests (too noisy)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return None

            # Skip non-GET/POST requests for dashboard purposes
            if request.method not in ['GET', 'POST']:
                return None

            # Get current tenant for multi-tenant tracking
            from dose.utils import get_current_tenant
            current_tenant = get_current_tenant(request)

            # Record the request with tenant context
            UserRequestTracker.record_request(request.user, request, tenant=current_tenant)

        except Exception as e:
            # Don't break the request if tracking fails
            logger.warning(f"Request tracking failed: {e}")

        return None

    def _should_exclude_path(self, path):
        """
        Check if path should be excluded from tracking
        """
        # Exact path matches
        if path in self.EXCLUDE_PATHS:
            return True

        # Prefix matches
        for prefix in self.EXCLUDE_PREFIXES:
            if path.startswith(prefix):
                return True

        return False