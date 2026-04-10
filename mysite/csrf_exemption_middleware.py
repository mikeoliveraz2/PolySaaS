"""
CSRF Exemption Middleware for Passthrough Paths

This middleware exempts passthrough paths (/pt/*) from Django's CSRF protection.
These paths are handled by the ExternalPassthroughMiddleware which forwards requests
to external services. Django's CSRF validation is not applicable to these requests.
"""

from django.utils.deprecation import MiddlewareMixin

from dose.middleware.debug import DebugStackMiddleware   # ← ADD THIS
from dose.passthrough.handlers.registry import any_handler_exempts_csrf_for_path

class CSRFExemptionMiddleware(DebugStackMiddleware, MiddlewareMixin):  # ← FIRST!

    """
    Middleware to exempt passthrough paths from Django CSRF protection.

    Passthrough paths (/pt/<context>/<service>/) are handled entirely by the
    ExternalPassthroughMiddleware and forwarded to external services. Django's CSRF
    protection should not apply to these paths since:

    1. The external service handles its own CSRF token validation
    2. The middleware bypasses Django views entirely
    3. The browser communicates directly with the external service for form submission
    """

    def process_request(self, request):
        """
        Mark passthrough requests as CSRF-exempt before Django's CSRF middleware processes them.
        """
        # Check if this is a passthrough request
        if self._is_passthrough_path(request.path_info):
            # Mark this request as exempt from CSRF checking
            # This must be set BEFORE the CSRF middleware processes the request
            request._dont_enforce_csrf_checks = True
            print(f"[CSRF EXEMPTION] Path {request.path_info} marked as CSRF-exempt")

        return None

    def _is_passthrough_path(self, path_info):
        """
        Check if the path is a passthrough path that should be CSRF-exempt.

        Passthrough paths follow the pattern: /pt/<context>/<service>/...
        Examples:
        - /pt/admin/odoo/
        - /pt/admin/odoo/web/login
        - /pt/dose/gmail/

        """
        # All /pt/ paths are passthrough infrastructure paths.
        if path_info.startswith('/pt/'):
            return True

        return any_handler_exempts_csrf_for_path(path_info)
