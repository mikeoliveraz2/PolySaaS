"""
Debug endpoint to capture exact OSTicket request/response for comparison
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json

@login_required
@csrf_exempt
@require_http_methods(["GET", "POST"])
def debug_osticket_request(request):
    """
    Capture and return exact request details for debugging
    """
    from dose.models import PassThroughEndpoint
    from dose.osticket_admin import get_osticket_session
    from urllib.parse import urlparse

    endpoint = PassThroughEndpoint.objects.filter(trigger_path__icontains='osticket').first()
    if not endpoint:
        return JsonResponse({'error': 'OSTicket endpoint not found'}, status=404)

    # Get session
    session = get_osticket_session()

    # Capture browser cookies
    browser_cookies = dict(request.COOKIES)

    # Sync to session (like our code does)
    for cookie_name in ['OSTSESSID', 'csrf_token']:
        if cookie_name in browser_cookies:
            session.cookies.set(cookie_name, browser_cookies[cookie_name])

    # Build target URL
    parsed = urlparse(endpoint.endpoint_url)
    target_base = f"{parsed.scheme}://{parsed.netloc}"
    target_path = parsed.path.rstrip('/')

    if request.path_info.startswith('/pt/'):
        parts = request.path_info.strip('/').split('/')
        if len(parts) >= 3:
            ext_path = '/'.join(parts[3:])
        else:
            ext_path = ''
    else:
        ext_path = request.path_info.replace(f'/admin/{endpoint.trigger_path}', '', 1)

    # Strip scp/ if endpoint already has it
    if 'osticket' in endpoint.trigger_path.lower():
        if '/scp/' in endpoint.endpoint_url or endpoint.endpoint_url.endswith('/scp'):
            if ext_path.startswith('scp/'):
                ext_path = ext_path[4:]
            elif ext_path == 'scp':
                ext_path = ''

    target_url = f"{target_base}{target_path}/{ext_path}".rstrip('/')
    if not target_url.endswith('/') and not ext_path:
        target_url += '/'

    # Capture request details
    request_details = {
        'method': request.method,
        'path': request.path_info,
        'target_url': target_url,
        'browser_cookies': {k: v[:50] + '...' if len(v) > 50 else v for k, v in browser_cookies.items()},
        'session_cookies_before': {k: v[:50] + '...' if len(str(v)) > 50 else str(v) for k, v in dict(session.cookies).items()},
    }

    if request.method == 'POST':
        request_details['post_data'] = {k: v[:50] + '...' if isinstance(v, str) and len(v) > 50 else v for k, v in request.POST.dict().items()}

        # Make actual request
        post_data = {key: request.POST.getlist(key) if len(request.POST.getlist(key)) > 1 else request.POST[key]
                    for key in request.POST}

        headers = {
            'User-Agent': request.META.get('HTTP_USER_AGENT', ''),
            'Referer': target_url,
        }

        response = session.post(
            target_url,
            data=post_data,
            headers=headers,
            timeout=30,
            allow_redirects=False,
            verify=False
        )

        request_details['response'] = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'has_access_denied': 'access denied' in response.text.lower() if hasattr(response, 'text') else False,
            'response_preview': response.text[:500] if hasattr(response, 'text') else '',
        }
        request_details['session_cookies_after'] = {k: v[:50] + '...' if len(str(v)) > 50 else str(v) for k, v in dict(session.cookies).items()}

    return JsonResponse(request_details, indent=2)

