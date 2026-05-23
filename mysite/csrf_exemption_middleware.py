# mysite/csrf_exemption_middleware.py
from django.utils.deprecation import MiddlewareMixin


class CSRFExemptionMiddleware(MiddlewareMixin):
    """Simple CSRF exemption for passthrough routes"""

    def process_request(self, request):
        path = request.path_info or request.path
        if path.startswith('/pt/'):
            # Bypass CSRF for all passthrough paths
            setattr(request, '_csrf_exempt', True)
            print(f"[CSRF] Exempted: {path}")
        return None