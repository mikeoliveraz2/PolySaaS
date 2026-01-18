"""
Diagnostic view to see exactly what's happening with OS Ticket requests
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import requests
from dose.models import PassThroughEndpoint
from dose.osticket_admin import get_osticket_session

@login_required
@csrf_exempt
@require_http_methods(["GET"])
def test_osticket_access(request):
    """
    Test OS Ticket access and return detailed diagnostic information
    """
    endpoint = PassThroughEndpoint.objects.filter(trigger_path__icontains='osticket').first()
    if not endpoint:
        return JsonResponse({'error': 'OS Ticket endpoint not found'}, status=404)

    # Get dashboard URL
    login_url = endpoint.endpoint_url
    if '/scp/login.php' not in login_url:
        base = login_url.split('/scp/')[0].rstrip('/') if '/scp/' in login_url else login_url.rstrip('/')
        login_url = f"{base}/scp/login.php"
    dashboard_url = login_url.replace('/login.php', '/dashboard.php')

    diagnostics = {
        'endpoint_id': endpoint.id,
        'endpoint_url': endpoint.endpoint_url,
        'dashboard_url': dashboard_url,
        'browser_cookies': dict(request.COOKIES),
        'discovered_subpaths': endpoint.discovered_subpaths,
    }

    # Test 1: Check browser cookies
    browser_has_session = any(name in request.COOKIES for name in ['OSTSESSID', 'SSSESSID'])
    diagnostics['browser_has_session_cookie'] = browser_has_session

    # Test 2: Check discovered_subpaths
    fresh_cookies = endpoint.discovered_subpaths.get("cookies", {}) if endpoint.discovered_subpaths else {}
    diagnostics['fresh_cookies_keys'] = list(fresh_cookies.keys()) if fresh_cookies else []
    diagnostics['has_fresh_session_cookie'] = any(name in fresh_cookies for name in ['OSTSESSID', 'SSSESSID'])

    # Test 3: Try accessing dashboard with browser cookies
    session = get_osticket_session()

    # Sync browser cookies to session
    for cookie_name in ['OSTSESSID', 'SSSESSID', 'csrf_token', '__CSRFToken__']:
        if cookie_name in request.COOKIES:
            session.cookies.set(cookie_name, request.COOKIES[cookie_name])

    # Also try fresh cookies if browser doesn't have them
    if not browser_has_session and fresh_cookies:
        for cookie_name in ['OSTSESSID', 'SSSESSID', '__CSRFToken__']:
            if cookie_name in fresh_cookies:
                session.cookies.set(cookie_name, fresh_cookies[cookie_name])

    diagnostics['session_cookies_before_request'] = dict(session.cookies)

    # Make request
    try:
        response = session.get(
            dashboard_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': dashboard_url,
            },
            timeout=10,
            verify=False
        )

        diagnostics['request_status'] = response.status_code
        diagnostics['request_url'] = response.url
        diagnostics['response_cookies'] = dict(response.cookies)
        diagnostics['response_length'] = len(response.text)
        diagnostics['response_preview'] = response.text[:500]

        # Check for access denied
        response_lower = response.text.lower()
        diagnostics['has_access_denied'] = 'access denied' in response_lower[:1000]
        diagnostics['has_login_redirect'] = 'login' in response_lower[:500] and 'dashboard' not in response_lower[:500]
        diagnostics['looks_successful'] = not diagnostics['has_access_denied'] and not diagnostics['has_login_redirect'] and response.status_code == 200

    except Exception as e:
        diagnostics['error'] = str(e)
        import traceback
        diagnostics['traceback'] = traceback.format_exc()

    return JsonResponse(diagnostics, indent=2)

