"""
PolySniffer Middleware — Server-side traffic capture for native/direct flows.
Works alongside the passthrough forwarder (which logs passthrough traffic).
No Chrome extension required.
"""
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
        from .models import TrafficLog

        duration = (time.time() - start) * 1000

        def truncate(text, max_len=8000):
            if not text:
                return ''
            text = str(text)
            return text[:max_len] + " [TRUNCATED]" if len(text) > max_len else text

        try:
            body = request.body.decode('utf-8', errors='ignore') if request.body else ''
        except Exception:
            body = ''

        try:
            resp_body = (
                response.content.decode('utf-8', errors='ignore')
                if hasattr(response, 'content') and response.content else ''
            )
        except Exception:
            resp_body = ''

        service = self._guess_service(request.path)
        correlation_id = getattr(request, '_polysniffer_correlation_id', '')

        TrafficLog.objects.create(
            capture_session=capture,
            capture_source=TrafficLog.CAPTURE_NATIVE,
            method=request.method,
            url=request.build_absolute_uri(),
            path=request.path,
            client_path=request.path,
            headers=dict(request.headers),
            cookies=dict(request.COOKIES),
            query_params=dict(request.GET),
            body=truncate(body),
            status_code=response.status_code,
            response_headers=dict(response.items()),
            response_body=truncate(resp_body),
            response_size=len(response.content) if hasattr(response, 'content') and response.content else 0,
            endpoint_name=f"{service}_native",
            service=service,
            correlation_id=correlation_id,
            user=request.user if request.user.is_authenticated else None,
            captured_at=timezone.now(),
            duration_ms=round(duration, 2),
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
