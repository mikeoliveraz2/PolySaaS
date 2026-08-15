"""

PolySniffer 2.0 — native (transparent) sniff forwarder.

"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION

# BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24

from __future__ import annotations



import time

from urllib.parse import urljoin, urlparse



import requests

from django.http import HttpResponse



from dose.polysniffer.har_capture import log_requests_response
from dose.polysniffer.sniff_handler_bridge import apply_native_sniff_rewrites
from dose.polysniffer.sniff_native_rewrite import filter_native_response_headers
from dose.polysniffer.sniff_tenant import bind_request_tenant, get_sniff_capture_session





def _resolve_upstream_url(endpoint_url: str, subpath: str) -> tuple[str, str]:

    base = (endpoint_url or '').rstrip('/')

    sub = subpath or '/'

    if not sub.startswith('/'):

        sub = '/' + sub

    if sub == '/':

        configured_path = urlparse(base).path or '/'

        return (base if configured_path != '/' else base + '/'), configured_path

    return base + sub, sub





def _outbound_headers(request) -> dict:

    skip = {

        'host', 'connection', 'content-length', 'transfer-encoding',

        'accept-encoding',

    }

    headers = {}

    for k, v in request.headers.items():

        if k.lower() not in skip:

            headers[k] = v

    headers['Accept-Encoding'] = 'identity'

    return headers





def forward_sniff_native(request, endpoint, subpath: str = '') -> HttpResponse:

    """

    Raw proxy for native sniff mode. Captures to TrafficLog when session active.

    """

    target_url, upstream_path = _resolve_upstream_url(endpoint.endpoint_url, subpath)

    upstream_query = request.GET.copy()
    upstream_query.pop('schema', None)
    upstream_query.pop('ps_sniff', None)
    if upstream_query:

        sep = '&' if '?' in target_url else '?'

        target_url += sep + upstream_query.urlencode()

    start = time.time()

    resp = requests.request(

        method=request.method,

        url=target_url,

        headers=_outbound_headers(request),

        data=request.body,

        cookies=dict(request.COOKIES),

        allow_redirects=False,

        timeout=60,

    )

    duration_ms = (time.time() - start) * 1000



    endpoint_host = urlparse(endpoint.endpoint_url).netloc
    service = (getattr(endpoint, 'provider', None) or endpoint_host or 'unknown')[:50]

    bind_request_tenant(request)
    session = get_sniff_capture_session(request, endpoint_host)
    if session:
        request._polysniffer_capture = session

    if session or getattr(request, '_polysniffer_capture', None):

        log_requests_response(

            request,

            resp,

            capture_source='native',

            target_url=target_url,

            upstream_path=upstream_path,

            endpoint_name=endpoint.menu_title or endpoint.endpoint_url or service,

            service=service,

            sniff_mode='native',

            duration_ms=duration_ms,

        )



    proxy_prefix = getattr(request, '_polysniffer_proxy_prefix', '') or (
        f"/dose/sniff/{getattr(endpoint, 'pk', '')}/native"
    )

    content = resp.content
    content_type = (resp.headers.get('Content-Type') or '').lower()
    if content_type.startswith('text/html'):
        content = apply_native_sniff_rewrites(
            content,
            content_type=content_type,
            request=request,
            endpoint=endpoint,
            upstream_path=upstream_path,
            proxy_prefix=proxy_prefix,
        )

    django_resp = HttpResponse(
        content=content,
        status=resp.status_code,
    )

    safe_headers = filter_native_response_headers(dict(resp.headers))
    location = safe_headers.get('Location')
    if location:
        endpoint_origin = urlparse(endpoint.endpoint_url)
        target = urlparse(urljoin(endpoint.endpoint_url, location))
        if (
            target.scheme == endpoint_origin.scheme
            and target.netloc == endpoint_origin.netloc
        ):
            target_path = target.path or '/'
            if target.query:
                target_path += f'?{target.query}'
            safe_headers['Location'] = f'{proxy_prefix}{target_path}'
    for k, v in safe_headers.items():
        django_resp[k] = v

    return django_resp


