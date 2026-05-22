"""
Chrome Extension API endpoints for PolySniffer.
These are called by the PolySniffer Chrome extension to list endpoints,
get CSRF tokens, and submit captures.
"""
import json
import logging
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.utils import timezone
from dose.models import PassThroughEndpoint, Tenant
from dose.polysniffer.models import TrafficEntry, TrafficCapture
from dose.utils.helpers import get_current_tenant

logger = logging.getLogger(__name__)


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


@csrf_exempt
@require_http_methods(["POST"])
def capture_endpoint(request):
    """
    POST /admin/polysniffer/api/capture/
    
    Receives browser-captured network entries from JavaScript instrumentation.
    Creates TrafficEntry records for analysis and comparison.
    
    Expected JSON payload:
    {
        "capture_id": "optional-session-id",  // Links to TrafficCapture session
        "entry_type": "fetch|xhr|websocket|navigation|other",
        "url": "https://example.com/api/endpoint",
        "method": "GET|POST|etc",
        "status_code": 200,
        "duration_ms": 123.45,
        "request_headers": {"Content-Type": "application/json"},
        "response_headers": {"Content-Type": "application/json"},
        "request_body": "optional request body",
        "response_body_preview": "optional response preview",
        "raw_entry": {}  // Complete original entry data
    }
    
    Returns:
    {
        "success": true,
        "entry_id": 123,
        "capture_id": "session-id"
    }
    """
    try:
        # Parse JSON body
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"[capture_endpoint] JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON in request body'
            }, status=400)
        
        # Get current tenant
        tenant = get_current_tenant(request)
        if not tenant:
            logger.error("[capture_endpoint] No tenant found for request")
            return JsonResponse({
                'success': False,
                'error': 'No tenant associated with this session'
            }, status=400)
        
        logger.info(f"[capture_endpoint] Processing capture for tenant: {tenant.name} (slug={tenant.slug})")
        
        # Get or create TrafficCapture session
        capture_id = data.get('capture_id')
        capture_session = None
        
        if capture_id:
            # Try to find existing capture session
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {tenant.schema_name},public;")
                capture_session = TrafficCapture.objects.filter(
                    tenant=tenant,
                    capture_name=capture_id
                ).first()
                
                if capture_session:
                    logger.info(f"[capture_endpoint] Using existing capture session: {capture_session.capture_name}")
            except Exception as e:
                logger.warning(f"[capture_endpoint] Error finding capture session: {e}")
        
        # Auto-create capture session if not found
        if not capture_session:
            capture_name = capture_id or f"browser-capture-{timezone.now().strftime('%Y%m%d-%H%M%S')}"
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {tenant.schema_name},public;")
                capture_session = TrafficCapture.objects.create(
                    tenant=tenant,
                    capture_name=capture_name,
                    is_active=True,
                    description="Browser-captured traffic session"
                )
                logger.info(f"[capture_endpoint] Created new capture session: {capture_session.capture_name}")
            except Exception as e:
                logger.error(f"[capture_endpoint] Error creating capture session: {e}")
                return JsonResponse({
                    'success': False,
                    'error': f'Failed to create capture session: {str(e)}'
                }, status=500)
        
        # Validate required fields
        required_fields = ['entry_type', 'url', 'method']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            logger.error(f"[capture_endpoint] Missing required fields: {missing_fields}")
            return JsonResponse({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=400)
        
        # Create TrafficEntry
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {tenant.schema_name},public;")
            
            entry = TrafficEntry.objects.create(
                tenant=tenant,
                capture=capture_session,
                timestamp=timezone.now(),
                entry_type=data.get('entry_type', 'other'),
                url=data.get('url', '')[:1000],  # Truncate to max length
                method=data.get('method', 'GET')[:10],
                status_code=data.get('status_code'),
                duration_ms=data.get('duration_ms', 0),
                request_headers=data.get('request_headers', {}),
                response_headers=data.get('response_headers', {}),
                request_body=data.get('request_body', ''),
                response_body_preview=data.get('response_body_preview', ''),
                raw_entry=data.get('raw_entry', data)  # Store complete data if raw_entry not provided
            )
            
            logger.info(
                f"[capture_endpoint] Created TrafficEntry #{entry.id}: "
                f"{entry.entry_type} {entry.method} {entry.url[:50]}... "
                f"(status={entry.status_code}, duration={entry.duration_ms}ms)"
            )
            
            return JsonResponse({
                'success': True,
                'entry_id': entry.id,
                'capture_id': capture_session.capture_name,
                'capture_session_id': capture_session.id,
                'tenant': tenant.slug
            })
            
        except Exception as e:
            logger.error(f"[capture_endpoint] Error creating TrafficEntry: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Failed to create traffic entry: {str(e)}'
            }, status=500)
    
    except Exception as e:
        logger.error(f"[capture_endpoint] Unexpected error: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }, status=500)
