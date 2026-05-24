# dose/passthrough/middleware.py
# GENERIC MIDDLEWARE - NO ENDPOINT SPECIFIC CODE
import logging
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ExternalPassthroughMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._is_passthrough_request(request):
            response = self._handle_passthrough(request)
            if response is not None:
                return response
        return self.get_response(request)

    def _is_passthrough_request(self, request):
        return request.path.startswith('/pt/admin/') or request.path.startswith('/pt/dose/')

    def _handle_passthrough(self, request):
        try:
            trigger = self._extract_trigger(request)
            if not trigger:
                return None

            from dose.passthrough.handlers.registry import get_handler
            handler = get_handler(trigger)

            if not handler:
                print(f"[PT-MW] No handler for trigger: {trigger}")
                return None

            print(f"[PT-MW] Using handler: {handler.__class__.__name__} for {trigger}")

            if hasattr(handler, 'handle_request'):
                result = handler.handle_request(request, None)
                if result is not None:
                    return result

            # Fallback to forwarding
            from dose.passthrough.forwarding import forward_request_standardized
            return forward_request_standardized(request, None, handler=handler)

        except Exception as e:
            logger.error(f"Passthrough middleware error: {e}", exc_info=True)
            return HttpResponse(f"Passthrough Error: {e}", status=500)

    def _extract_trigger(self, request):
        parts = request.path.strip('/').split('/')
        if len(parts) >= 3 and parts[0] == 'pt' and parts[1] == 'admin':
            return parts[2]
        return None