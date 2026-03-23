"""Lightweight health endpoint for load balancers (Railway, k8s, etc.)."""
from django.http import HttpResponse


def health_live(request):
    """Liveness: process is up; no database."""
    return HttpResponse("ok", content_type="text/plain")


def health_ready(request):
    """Readiness: verify database connection when requested."""
    from django.db import connection
    try:
        connection.ensure_connection()
    except Exception as exc:
        return HttpResponse(f"db_unavailable: {exc}", status=503, content_type="text/plain")
    return HttpResponse("ready", content_type="text/plain")
