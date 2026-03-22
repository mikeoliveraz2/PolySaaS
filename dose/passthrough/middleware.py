# dose/passthrough/middleware.py — FINAL — OUT = LAST, IN = FIRST — CHIEF ARCHITECT APPROVED
import logging
from django.utils.deprecation import MiddlewareMixin
from dose.models import PassThroughEndpoint
from dose.passthrough.forwarding import forward_request_standardized
from dose.passthrough.handlers.registry import get_handler_for_endpoint

logger = logging.getLogger(__name__)

class ExternalPassthroughMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def __call__(self, request):
        """
        REQUEST PHASE — runs for every request
        This is the LAST middleware before the request leaves Django
        -> Perfect place for PASSTHROUGH-OUT
        """
        if request.path_info.startswith("/pt/"):
            parts = request.path_info.strip("/").split("/")
            print(f"[PT-MIDDLEWARE] path={request.path_info} parts={parts}")
            if len(parts) >= 3 and parts[0] == "pt":
                trigger = parts[2]
                print(f"[PT-MIDDLEWARE] trigger={trigger}")

                endpoint = PassThroughEndpoint.objects.filter(
                    trigger_path__iexact=trigger,
                    is_enabled=True
                ).first()
                print(f"[PT-MIDDLEWARE] endpoint={endpoint}")

                if endpoint:
                    print("\n" + "="*120)
                    print("PASSTHROUGH-OUT -> SENDING TO EXTERNAL SERVICE (LAST BEFORE EXIT)")
                    print(f"TARGET URL: {endpoint.endpoint_url}")
                    print(f"PATH      : {request.path_info}")
                    print(f"USER      : {request.user}")
                    print("="*120 + "\n")

                    handler = get_handler_for_endpoint(endpoint, request)
                    response = forward_request_standardized(request, endpoint.endpoint_url, handler=handler)

                    # Mark so process_response knows it was us
                    request._passthrough_handled = True
                    request._passthrough_response = response

                    return response  # SHORT-CIRCUIT — WE ARE DONE

        # Not a passthrough request — continue down the stack
        return self.get_response(request)

    def process_response(self, request, response):
        """
        RESPONSE PHASE — runs for every response
        This is the FIRST middleware that sees the response coming back
        -> Perfect place for PASSTHROUGH-IN
        """
        if getattr(request, '_passthrough_handled', False):
            print("\n" + "="*120)
            print("PASSTHROUGH-IN <- RESPONSE RECEIVED (FIRST ON RETURN)")
            print(f"STATUS: {response.status_code}")
            print(f"CONTENT LENGTH: {len(response.content) if hasattr(response, 'content') else 'unknown'} bytes")
            preview = response.content[:500].decode('utf-8', errors='ignore') if hasattr(response, 'content') else "No content"
            print(f"PREVIEW: {preview}")
            print("="*120 + "\n")

        return response