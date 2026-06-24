"""
PolySniffer Middleware — Server-side traffic capture for native/direct flows.
Works alongside the passthrough forwarder (which logs passthrough traffic).
No Chrome extension required.
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 — 2026-06-24
import time
import uuid
from django.utils import timezone


class PolySnifferMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Passthrough paths are already logged by the forwarder;
        # skip them here to avoid duplicate noisy capture.
        if '/pt/admin/' in request.path:
            return self.get_response(request)

        # PolySniffer 2.0 sniff paths are logged by sniff_forward / forwarder.
        if '/dose/sniff/' in request.path:
            return self.get_response(request)

        # Only capture when an active TrafficCapture session exists for this tenant.
        capture = self._get_active_capture(request)
        if not capture:
            return self.get_response(request)

        start = time.time()
        request._polysniffer_capture = capture
        request._polysniffer_correlation_id = str(uuid.uuid4())[:12]

        response = self.get_response(request)

        # Log request/response pair atomically after response is ready.
        self._log_traffic(request, response, capture, start)

        return response

    def _get_active_capture(self, request):
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return None
        from .models import TrafficCapture
        return TrafficCapture.objects.filter(
            tenant=tenant,
            is_active=True,
            expires_at__gt=timezone.now()
        ).first()

    def _log_traffic(self, request, response, capture, start):
        from dose.polysniffer.har_capture import log_django_response

        service = self._guess_service(request.path)
        log_django_response(
            request,
            response,
            capture_source='native',
            target_url=request.build_absolute_uri(),
            endpoint_name=f'{service}_native',
            service=service,
            sniff_mode='native',
            start_time=start,
        )

    def _guess_service(self, path):
        path_lower = path.lower()
        if 'mattermost' in path_lower:
            return 'mattermost'
        if 'odoo' in path_lower:
            return 'odoo'
        if 'nextcloud' in path_lower:
            return 'nextcloud'
        return 'polysaas'
