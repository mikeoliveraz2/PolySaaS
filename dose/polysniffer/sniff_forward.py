"""

PolySniffer 2.0 — native (transparent) sniff forwarder.

"""

# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION

# BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24

from __future__ import annotations



import time

from urllib.parse import urlparse



import requests

from django.http import HttpResponse



from dose.polysniffer.har_capture import log_requests_response
from dose.polysniffer.sniff_tenant import bind_request_tenant, get_sniff_capture_session
from dose.polysniffer.sniff_native_rewrite import (

    filter_native_response_headers,

)





def _resolve_upstream_url(endpoint_url: str, subpath: str) -> tuple[str, str]:

    base = (endpoint_url or '').rstrip('/')

    sub = subpath or '/'

    if not sub.startswith('/'):

        sub = '/' + sub

    if sub == '/':

        return base + '/', '/'

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

    Raw proxy for native sniff mode. Captures the upstream exchange unchanged.

    Native must not resolve production handlers or rewrite endpoint content.

    """

    target_url, upstream_path = _resolve_upstream_url(endpoint.endpoint_url, subpath)

    if request.GET:

        sep = '&' if '?' in target_url else '?'

        target_url += sep + request.GET.urlencode()

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



    service = (urlparse(endpoint.endpoint_url or '').netloc or 'unknown')[:50]

    bind_request_tenant(request)
    session = get_sniff_capture_session(request, endpoint.id)
    if session:
        request._polysniffer_capture = session

    if session or getattr(request, '_polysniffer_capture', None):

        log_requests_response(

            request,

            resp,

            capture_source='native',

            target_url=target_url,

            upstream_path=upstream_path,

            endpoint_name=endpoint.menu_title or service,

            service=service,

            sniff_mode='native',

            duration_ms=duration_ms,

        )



    content_type = resp.headers.get('Content-Type', 'application/octet-stream')

    django_resp = HttpResponse(

        content=resp.content,

        status=resp.status_code,

        content_type=content_type,

    )

    hop_by_hop = {'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',

                  'te', 'trailers', 'transfer-encoding', 'upgrade', 'content-encoding'}

    for k, v in filter_native_response_headers(dict(resp.headers)).items():

        if k.lower() not in hop_by_hop:

            django_resp[k] = v



    return django_resp


