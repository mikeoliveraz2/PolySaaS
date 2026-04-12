import os

from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin


class AdminStatusBannerMiddleware(MiddlewareMixin):
    """Show a one-time green status banner in /admin/ for staff users."""

    def process_request(self, request):
        if not request.path.startswith("/admin/"):
            return None

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or not user.is_staff:
            return None

        if os.environ.get("ADMIN_STATUS_BANNER_ENABLED", "1").strip() != "1":
            return None

        message_text = os.environ.get(
            "ADMIN_STATUS_BANNER_TEXT",
            "Status: tenant admin bootstrap is enabled.",
        ).strip()
        if not message_text:
            return None

        seen_key = f"admin_status_banner_seen:{message_text}"
        if request.session.get(seen_key):
            return None

        messages.success(request, message_text)
        request.session[seen_key] = True
        return None
