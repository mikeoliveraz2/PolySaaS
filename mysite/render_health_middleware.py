"""Answer Render / load-balancer liveness without touching the DB or full middleware chain.

Internal probes are often plain HTTP without ``X-Forwarded-Proto``; they must get 200 from
``/health/`` even when PostgreSQL is still starting or ``SECURE_SSL_REDIRECT`` would
otherwise redirect bare HTTP requests.
"""

from django.http import HttpResponse


class RenderLivenessMiddleware:
    """Return 200 for ``GET /health/`` before SecurityMiddleware and tenant/session DB work."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "GET" and request.path == "/health/":
            return HttpResponse("ok", content_type="text/plain")
        return self.get_response(request)
