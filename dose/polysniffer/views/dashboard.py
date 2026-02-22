# dose/polysniffer/views/dashboard.py - 2026-01-17 22:35 PST

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.utils import timezone
from ..models import TrafficLog
from .core import get_endpoint_any_schema
from urllib.parse import urlparse
import json

@staff_member_required
def debug_dashboard(request):
    """
    Debug dashboard - shows all captured traffic logs
    Only accessible from within sniffer interface
    """
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Staff access required')
    logs = TrafficLog.objects.all().order_by('-timestamp')[:100]
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    context = {
        'logs': page_obj,
        'total_logs': logs.count(),
        'page_obj': page_obj
    }
    return render(request, 'polysniffer/dashboard.html', context)

@staff_member_required
def view_log(request, log_id):
    """
    View detailed log entry
    """
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Staff access required')
    log = get_object_or_404(TrafficLog, id=log_id)
    context = {'log': log}
    return render(request, 'polysniffer/log_detail.html', context)

@staff_member_required
def export_har(request, log_id=None):
    """
    Export captured traffic as HAR (HTTP Archive) format
    """
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('Staff access required')

    if log_id:
        logs = TrafficLog.objects.filter(id=log_id)
    else:
        logs = TrafficLog.objects.all().order_by('-timestamp')[:100]

    har_data = {
        "log": {
            "version": "1.2",
            "creator": {
                "name": "PolySniffer",
                "version": "1.0"
            },
            "entries": []
        }
    }

    for log in logs:
        entry = {
            "startedDateTime": log.timestamp.isoformat(),
            "time": 0,
            "request": {
                "method": log.method,
                "url": log.url,
                "httpVersion": "HTTP/1.1",
                "headers": json.loads(log.request_headers) if log.request_headers else [],
                "queryString": [],
                "postData": {
                    "mimeType": "application/json",
                    "text": log.request_body
                } if log.request_body else None,
                "headersSize": -1,
                "bodySize": -1
            },
            "response": {
                "status": log.status_code,
                "statusText": "",
                "httpVersion": "HTTP/1.1",
                "headers": json.loads(log.response_headers) if log.response_headers else [],
                "content": {
                    "size": -1,
                    "mimeType": "application/json",
                    "text": log.response_body
                } if log.response_body else None,
                "headersSize": -1,
                "bodySize": -1
            },
            "cache": {},
            "timings": {
                "send": -1,
                "wait": -1,
                "receive": -1
            }
        }
        har_data["log"]["entries"].append(entry)

    response = HttpResponse(json.dumps(har_data, indent=2), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="polysniffer_export.har"'
    return response

@csrf_exempt
@require_http_methods(["POST"])
@staff_member_required
def capture_traffic(request):
    """
    Generic capture endpoint for logging traffic
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Staff access required'}, status=403)

    try:
        data = json.loads(request.body)
        capture_data = data

        # Log the capture
        TrafficLog.objects.create(
            endpoint=None,  # Generic capture
            method=capture_data.get('method', 'GET'),
            url=capture_data.get('url', ''),
            status_code=capture_data.get('status', 0),
            request_headers=json.dumps(capture_data.get('headers', {})),
            request_body=json.dumps(capture_data.get('body', '')),
            response_headers=json.dumps({}),
            response_body=json.dumps(capture_data.get('data', {})),
            captured_at=timezone.now()
        )

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error capturing traffic: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@staff_member_required
def save_capture(request, endpoint_id):
    """
    Save captured data to endpoint and create TrafficLog entries for AI analysis.
    Called by both the Django admin UI and the Chrome extension.
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Staff access required'}, status=403)

    endpoint = get_endpoint_any_schema(endpoint_id, request)

    try:
        data = json.loads(request.body)
        captures = data.get('captures', [])

        if not captures:
            return JsonResponse({
                'success': False,
                'error': 'No captures to save'
            }, status=400)

        latest = captures[-1]
        endpoint.polysniffer_debug_output = json.dumps(latest, indent=2)
        endpoint.polysniffer_last_run = timezone.now()
        endpoint.save()

        log_count = 0
        for capture in captures:
            try:
                TrafficLog.objects.create(
                    method=capture.get('method', 'GET'),
                    url=capture.get('url', ''),
                    path=capture.get('url', '').split('?')[0].split('#')[0],
                    headers=capture.get('headers', {}),
                    cookies=capture.get('cookies', {}),
                    body=capture.get('body', '') if isinstance(capture.get('body'), str) else json.dumps(capture.get('body', '')),
                    status_code=capture.get('status', 0),
                    response_headers={},
                    response_body=json.dumps(capture.get('data', {})) if capture.get('data') else '',
                    endpoint_name=endpoint.trigger_path or str(endpoint),
                    user=request.user,
                    captured_at=timezone.now(),
                )
                log_count += 1
            except Exception:
                pass

        source = data.get('source', 'admin')
        return JsonResponse({
            'success': True,
            'message': f'Saved {len(captures)} capture(s), created {log_count} traffic log(s) [source: {source}]'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error saving captures: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@staff_member_required
def log_capture_to_services(request, endpoint_id):
    """
    Log captured data to TrafficLog model
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Staff access required'}, status=403)

    endpoint = get_endpoint_any_schema(endpoint_id, request)

    try:
        data = json.loads(request.body)
        captures = data.get('captures', [])

        # Log to TrafficLog model
        for capture in captures:
            TrafficLog.objects.create(
                endpoint=endpoint,
                method=capture.get('method', 'GET'),
                url=capture.get('url', ''),
                status_code=capture.get('status', 0),
                request_headers=json.dumps(capture.get('headers', {})),
                request_body=json.dumps(capture.get('body', '')),
                response_headers=json.dumps({}),
                response_body=json.dumps(capture.get('data', {})),
                captured_at=timezone.now()
            )

        return JsonResponse({
            'success': True,
            'message': f'Logged {len(captures)} captures to database'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error logging captures: {str(e)}'
        }, status=500)

@staff_member_required
def get_captures(request, endpoint_id):
    """
    Get captured requests for an endpoint, with optional since_id for polling
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Staff access required'}, status=403)

    endpoint = get_endpoint_any_schema(endpoint_id, request)
    endpoint_name = endpoint.menu_title or endpoint.trigger_path or str(endpoint_id)

    try:
        since_id = int(request.GET.get('since_id', 0))
        qs = TrafficLog.objects.filter(endpoint_name__iexact=endpoint_name)
        if not qs.exists():
            qs = TrafficLog.objects.all()
        if since_id:
            qs = qs.filter(id__gt=since_id)
        logs = qs.order_by('-captured_at')[:100]

        captures = []
        for log in logs:
            captures.append({
                'id': log.id,
                'method': log.method,
                'url': log.url,
                'path': log.path,
                'status_code': log.status_code,
                'headers': log.headers if isinstance(log.headers, dict) else {},
                'cookies': log.cookies if isinstance(log.cookies, dict) else {},
                'body': log.body or '',
                'captured_at': log.captured_at.strftime('%H:%M:%S') if log.captured_at else '',
            })

        return JsonResponse({
            'success': True,
            'captures': captures
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error retrieving captures: {str(e)}'
        }, status=500)

@staff_member_required
def apply_latest_capture(request, endpoint_id):
    """
    Apply latest capture data to modify handler
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Staff access required'}, status=403)

    endpoint = get_endpoint_any_schema(endpoint_id, request)

    try:
        # Get the latest capture
        latest_log = TrafficLog.objects.filter(endpoint=endpoint).order_by('-captured_at').first()
        if not latest_log:
            return JsonResponse({
                'success': False,
                'error': 'No captures found for this endpoint'
            }, status=404)

        # Apply the capture data to modify the handler
        capture_data = json.loads(latest_log.request_body) if latest_log.request_body else {}

        # Here you would modify the handler based on the captured data
        # For now, just return the data
        return JsonResponse({
            'success': True,
            'capture': capture_data,
            'message': 'Latest capture applied (handler modification logic would go here)'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error applying capture: {str(e)}'
        }, status=500)

@staff_member_required
def test_osticket_access(request):
    """
    Test osTicket access with stored cookies
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Staff access required'}, status=403)

    try:
        # Find osTicket endpoint
        from dose.models import PassThroughEndpoint
        from django.db import connection
        from dose.utils import get_current_tenant

        endpoint = None
        tenant = get_current_tenant(request) if request else None
        search_paths = []
        if tenant and tenant.schema_name:
            search_paths.append(tenant.schema_name)
        search_paths.append('public')

        for schema in search_paths:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {schema},public;")
                    endpoints = PassThroughEndpoint.objects.filter(
                        trigger_path__icontains='osticket'
                    ) | PassThroughEndpoint.objects.filter(
                        endpoint_url__icontains='/scp/'
                    ) | PassThroughEndpoint.objects.filter(
                        endpoint_url__icontains='supportsystem'
                    )
                    endpoint = endpoints.first()
                    if endpoint:
                        break
            except Exception:
                continue

        if not endpoint:
            return JsonResponse({
                'success': False,
                'error': 'No osTicket endpoint found'
            }, status=404)

        # Test access with stored cookies
        import requests
        session = requests.Session()
        parsed_endpoint = urlparse(endpoint.endpoint_url)

        if 'osticket_cookies' in request.session:
            for name, value in request.session['osticket_cookies'].items():
                session.cookies.set(name, value, domain=parsed_endpoint.netloc)

        # Try to access a protected page
        test_url = endpoint.endpoint_url.rstrip('/') + '/scp/'
        response = session.get(test_url, allow_redirects=False)

        return JsonResponse({
            'success': True,
            'status_code': response.status_code,
            'url': test_url,
            'has_cookies': bool(request.session.get('osticket_cookies')),
            'message': 'osTicket access test completed'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error testing osTicket access: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@staff_member_required
def silent_capture(request, endpoint_id):
    """
    Silent capture endpoint for background logging
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Staff access required'}, status=403)

    try:
        data = json.loads(request.body)
        endpoint = get_endpoint_any_schema(endpoint_id, request)
        endpoint_name = endpoint.menu_title or endpoint.trigger_path or str(endpoint_id)

        raw_url = str(data.get('url', ''))[:500]
        raw_method = str(data.get('method', 'GET'))[:10].upper()
        if raw_method in ('XMLHTTPREQUEST', 'SCRIPT', 'STYLESHEET', 'IMAGE', 'FONT', 'MAIN_FRAME', 'SUB_FRAME', 'OTHER'):
            raw_method = 'GET'
        raw_path = ''
        try:
            raw_path = urlparse(raw_url).path[:500]
        except Exception:
            raw_path = raw_url[:500]

        # URLField requires a valid URL; fall back to placeholder if invalid
        if not raw_url.startswith(('http://', 'https://')):
            raw_url = endpoint.endpoint_url or f'http://localhost/{raw_url}'

        TrafficLog.objects.create(
            endpoint_name=endpoint_name,
            method=raw_method or 'GET',
            url=raw_url,
            path=raw_path,
            headers=data.get('headers', {}),
            cookies=data.get('cookies', {}),
            body=json.dumps(data.get('body', data)),
            status_code=int(data.get('status', 0) or 0),
            response_headers={},
            response_body='',
            user=request.user if request.user.is_authenticated else None,
            captured_at=timezone.now()
        )

        return JsonResponse({'success': True})
    except Exception as e:
        import traceback
        print(f"[POLYSNIFFER] silent_capture ERROR: {str(e)}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Error in silent capture: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
@staff_member_required
def sync_v0_cookies(request, endpoint_id):
    """
    Sync V0.dev cookies from session
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Staff access required'}, status=403)

    endpoint = get_endpoint_any_schema(endpoint_id, request)

    try:
        # Forward cookies from session to endpoint
        if 'v0_dev_cookies' in request.session:
            import requests
            session = requests.Session()
            parsed_endpoint = urlparse(endpoint.endpoint_url)
            for name, value in request.session['v0_dev_cookies'].items():
                session.cookies.set(name, value, domain=parsed_endpoint.netloc)

            # Test the connection
            response = session.get(endpoint.endpoint_url)
            if response.status_code == 200:
                return JsonResponse({
                    'success': True,
                    'message': 'V0.dev cookies synced successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Cookie sync failed with status {response.status_code}'
                }, status=400)
        else:
            return JsonResponse({
                'success': False,
                'error': 'No V0.dev cookies found in session'
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error syncing cookies: {str(e)}'
        }, status=500)