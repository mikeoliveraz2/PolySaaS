"""
Chrome Extension API endpoints for PolySniffer.
These are called by the PolySniffer Chrome extension to list endpoints,
get CSRF tokens, and submit captures.
"""
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods
from django.db import connection
from dose.models import PassThroughEndpoint


@staff_member_required
def list_endpoints(request):
    """
    GET /admin/polysniffer/api/endpoints/
    Returns all enabled passthrough endpoints for the Chrome extension dropdown.
    """
    endpoints = []
    try:
        for ep in PassThroughEndpoint.objects.filter(is_enabled=True).order_by('trigger_path'):
            endpoints.append({
                'id': ep.id,
                'name': str(ep),
                'trigger_path': ep.trigger_path or '',
                'url': ep.endpoint_url or '',
                'has_captures': bool(getattr(ep, 'polysniffer_last_run', None)),
            })
    except Exception:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public;")
                for ep in PassThroughEndpoint.objects.filter(is_enabled=True).order_by('trigger_path'):
                    endpoints.append({
                        'id': ep.id,
                        'name': str(ep),
                        'trigger_path': ep.trigger_path or '',
                        'url': ep.endpoint_url or '',
                        'has_captures': False,
                    })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({
        'success': True,
        'endpoints': endpoints,
        'count': len(endpoints)
    })


@staff_member_required
def csrf_token(request):
    """
    GET /admin/polysniffer/api/csrf-token/
    Returns a CSRF token for the Chrome extension to use in POST requests.
    """
    return JsonResponse({
        'success': True,
        'token': get_token(request)
    })
