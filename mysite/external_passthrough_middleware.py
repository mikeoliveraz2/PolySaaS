# dose/passthrough/middleware.py — FINAL — YOUR ORIGINAL DESIGN — RAW LOGS
import logging
from django.utils.deprecation import MiddlewareMixin
from dose.models import PassThroughEndpoint
from dose.passthrough.forwarding import forward_request_standardized
from dose.passthrough.handlers import get_handler_for_endpoint
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

from dose.middleware.debug import DebugStackMiddleware   # ← ADD THIS

class ExternalPassthroughMiddleware(DebugStackMiddleware, MiddlewareMixin):  # ← FIRST!

    # Known Odoo path prefixes that indicate a request is for Odoo
    ODOO_PATH_PREFIXES = (
        '/web',
        '/api',
        '/bus',
        '/calendar',
        '/assets',
        '/purchase',
        '/stock',
        '/accounting',
        '/crm',
        '/sale',
        '/hr',
        '/project',
        '/website',
        '/ecommerce',
        '/mail',
        '/social',
        '/iot',
        '/iot_handlers',
        '/static',
        '/download',
        '/web_unsupported',
    )

    def process_request(self, request):
        path = request.path_info

        # YOUR ORIGINAL RAW LOG — BEFORE ANYTHING
        print("\n" + "="*120)
        print("PASSTHROUGH-OUT → INCOMING REQUEST")
        print(f"PATH: {path}")
        print(f"FULL URL: {request.build_absolute_uri()}")
        print(f"HEADERS: {dict(request.headers)}")
        print("="*120)

        # NATIVE ODOO PATH REWRITE
        # If path is /web/... or /api/... (Odoo-native, not /pt/...), rewrite it to
        # /pt/admin/{endpoint_url_hostname}/{path} so it matches the passthrough URL pattern.
        if any(path.startswith(p) for p in self.ODOO_PATH_PREFIXES) and not path.startswith('/pt/'):
            try:
                tenant = getattr(request, 'tenant', None)
                if tenant:
                    # Find Odoo endpoint for this tenant
                    odoo_endpoints = PassThroughEndpoint.objects.filter(
                        is_enabled=True
                    ).exclude(endpoint_url='')
                    
                    for ep in odoo_endpoints:
                        # Check if this endpoint is for Odoo by looking at the handler
                        handler = get_handler_for_endpoint(ep, request)
                        if handler and hasattr(handler, '__class__') and 'Odoo' in handler.__class__.__name__:
                            # Extract hostname from endpoint_url to use as trigger
                            parsed_url = urlparse(ep.endpoint_url)
                            hostname = parsed_url.netloc or parsed_url.hostname
                            if hostname:
                                # Rewrite path: /web/foo -> /pt/admin/{hostname}/web/foo
                                rewritten_path = f'/pt/admin/{hostname}{path}'
                                request.path_info = rewritten_path
                                print(f"[NATIVE ODOO PATH REWRITE] {path} → {rewritten_path}")
                                break
            except Exception as e:
                logger.warning(f"Native Odoo path rewrite failed: {e}", exc_info=True)
                print(f"[NATIVE ODOO PATH REWRITE ERROR] {e}")

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