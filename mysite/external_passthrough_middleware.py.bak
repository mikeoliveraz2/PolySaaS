# dose/passthrough/middleware.py — FINAL — YOUR ORIGINAL DESIGN — RAW LOGS
import logging
from django.utils.deprecation import MiddlewareMixin
from dose.models import PassThroughEndpoint
from dose.passthrough.forwarding import forward_request_standardized
from dose.passthrough.handlers import get_handler_for_endpoint

logger = logging.getLogger(__name__)

from dose.middleware.debug import DebugStackMiddleware   # ← ADD THIS

class ExternalPassthroughMiddleware(DebugStackMiddleware, MiddlewareMixin):  # ← FIRST!

    def process_request(self, request):
        path = request.path_info

        # YOUR ORIGINAL RAW LOG — BEFORE ANYTHING
        print("\n" + "="*120)
        print("PASSTHROUGH-OUT → INCOMING REQUEST")
        print(f"PATH: {path}")
        print(f"FULL URL: {request.build_absolute_uri()}")
        print(f"HEADERS: {dict(request.headers)}")
        print("="*120)

        if path.startswith('/pt/'):
            # Extract the trigger path from /pt/{trigger_path}
            # For /pt/admin/nextcloud/ -> /admin/nextcloud/
            trigger_path = '/' + path[4:]  # Remove '/pt/' prefix

            endpoint = PassThroughEndpoint.objects.filter(
                trigger_path__iexact=trigger_path,
                is_enabled=True
            ).first()

            if endpoint:
                print(f"PASSTHROUGH-OUT → MATCHED ENDPOINT: {endpoint.endpoint_url}")
                handler = get_handler_for_endpoint(endpoint, request)
                response = forward_request_standardized(request, endpoint.endpoint_url, handler=handler)

                # YOUR ORIGINAL RAW RETURN LOG — BEFORE ANYONE TOUCHES IT
                print("\n" + "="*120)
                print("PASSTHROUGH-IN ← RAW RESPONSE FROM SERVICE")
                print(f"STATUS: {response.status_code}")
                print(f"HEADERS: {dict(response.headers)}")
                if hasattr(response, 'content'):
                    print(f"CONTENT PREVIEW: {response.content[:500]}")
                print("="*120 + "\n")

                return response
            else:
                print(f"PASSTHROUGH-OUT → NO ENDPOINT FOUND for trigger_path: {trigger_path}")
                # Continue to normal processing - will likely result in 404

        return None