"""
PolySniffer 2.0 — native (transparent) sniff forwarder.
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 — 2026-06-24
from __future__ import annotations

import re
import time
from urllib.parse import urlencode, urlparse

import requests
from django.http import HttpResponse

from dose.polysniffer.har_capture import get_active_capture_session, log_requests_response


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


def _rewrite_location(location: str, proxy_prefix: str, endpoint_url: str) -> str:
    if not location:
        return proxy_prefix + '/'
    parsed_ep = urlparse(endpoint_url)
    upstream_origin = f'{parsed_ep.scheme}://{parsed_ep.netloc}'
    if location.startswith(upstream_origin):
        rest = location[len(upstream_origin):] or '/'
        if not rest.startswith('/'):
            rest = '/' + rest
        return proxy_prefix + rest
    if location.startswith('/'):
        return proxy_prefix + location
    return location


def forward_sniff_native(request, endpoint, subpath: str = '') -> HttpResponse:
    """
    Transparent proxy for native sniff mode. Captures to TrafficLog when session active.
    """
    target_url, upstream_path = _resolve_upstream_url(endpoint.endpoint_url, subpath)
    if request.GET:
        sep = '&' if '?' in target_url else '?'
        target_url += sep + urlencode(request.META.get('QUERY_STRING', ''))

    proxy_prefix = request.path_info.rsplit('/', 1)[0]
    if upstream_path != '/':
        # strip trailing path segment from prefix — rebuild from sniff base
        m = re.match(r'^(/dose/sniff/\d+/native)', request.path_info)
        proxy_prefix = m.group(1) if m else proxy_prefix

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

    service = (getattr(endpoint, 'provider', None) or endpoint.trigger_path or 'unknown')[:50]
    session = get_active_capture_session(request, endpoint.id)
    if session or getattr(request, '_polysniffer_capture', None):
        log_requests_response(
            request,
            resp,
            capture_source='native',
            target_url=target_url,
            upstream_path=upstream_path,
            endpoint_name=endpoint.menu_title or endpoint.trigger_path or service,
            service=service,
            sniff_mode='native',
            duration_ms=duration_ms,
        )

    django_resp = HttpResponse(
        content=resp.content,
        status=resp.status_code,
        content_type=resp.headers.get('Content-Type', 'application/octet-stream'),
    )
    hop_by_hop = {'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
                  'te', 'trailers', 'transfer-encoding', 'upgrade', 'content-encoding'}
    for k, v in resp.headers.items():
        if k.lower() not in hop_by_hop:
            django_resp[k] = v

    if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
        loc = resp.headers.get('Location', '/')
        django_resp['Location'] = _rewrite_location(loc, proxy_prefix, endpoint.endpoint_url)

    return django_resp
