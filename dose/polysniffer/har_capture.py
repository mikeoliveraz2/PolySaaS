"""
PolySniffer 2.0 — shared HAR / TrafficLog capture engine.
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 — 2026-06-24
from __future__ import annotations

import hashlib
import logging
import time
import uuid
from typing import Any, Optional

from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.utils import timezone

logger = logging.getLogger(__name__)

_BODY_TRUNCATE = 8000


def truncate_text(text: Any, max_len: int = _BODY_TRUNCATE) -> str:
    if not text:
        return ''
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[:max_len] + ' [TRUNCATED]'


def capture_user_in_current_schema(user):
    if not user or isinstance(user, AnonymousUser):
        return None
    return user if user.__class__._default_manager.filter(pk=user.pk).exists() else None


def get_active_capture_session(request, endpoint_id: Optional[int] = None):
    """Return active TrafficCapture for tenant, optionally matching endpoint id in name."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return None
    from dose.polysniffer.models import TrafficCapture

    qs = TrafficCapture.objects.filter(
        tenant=tenant,
        is_active=True,
        expires_at__gt=timezone.now(),
    ).order_by('-created_at')
    if endpoint_id is not None:
        prefix = f'ep{endpoint_id}-'
        match = qs.filter(capture_name__startswith=prefix).first()
        if match:
            return match
    return qs.first()


def _ensure_tenant_schema(tenant) -> None:
    if not tenant:
        return
    try:
        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{tenant.schema_name}", public;')
    except Exception as exc:
        logger.warning('har_capture: search_path failed: %s', exc)


def build_har_entry(
    *,
    method: str,
    url: str,
    path: str,
    headers: dict,
    cookies: dict,
    query_params: dict,
    body: str,
    status_code: int,
    response_headers: dict,
    response_body: str,
    response_size: int,
    duration_ms: float,
    captured_at=None,
    sniff_mode: str = '',
) -> dict:
    captured_at = captured_at or timezone.now()
    entry = {
        'startedDateTime': captured_at.isoformat(),
        'time': duration_ms,
        '_sniff_mode': sniff_mode,
        'request': {
            'method': method,
            'url': url,
            'httpVersion': 'HTTP/1.1',
            'headers': [{'name': k, 'value': str(v)} for k, v in (headers or {}).items()],
            'cookies': [{'name': k, 'value': str(v)} for k, v in (cookies or {}).items()],
            'queryString': [{'name': k, 'value': str(v)} for k, v in (query_params or {}).items()],
            'headersSize': -1,
            'bodySize': len(body.encode('utf-8')) if body else 0,
        },
        'response': {
            'status': status_code,
            'statusText': '',
            'httpVersion': 'HTTP/1.1',
            'headers': [{'name': k, 'value': str(v)} for k, v in (response_headers or {}).items()],
            'cookies': [],
            'content': {
                'size': response_size,
                'mimeType': (response_headers or {}).get('Content-Type', 'text/html'),
                'text': truncate_text(response_body, 10000),
            },
            'headersSize': -1,
            'bodySize': response_size,
        },
        'cache': {},
        'timings': {'wait': duration_ms, 'receive': 0},
    }
    if body:
        entry['request']['postData'] = {
            'mimeType': (headers or {}).get('Content-Type', 'application/octet-stream'),
            'text': body,
        }
    return entry


def log_http_exchange(
    request,
    *,
    method: str,
    url: str,
    path: str,
    client_path: str,
    capture_source: str,
    headers: dict,
    cookies: dict,
    query_params: dict,
    body: str,
    status_code: int,
    response_headers: dict,
    response_body: str,
    response_size: int,
    duration_ms: float,
    endpoint_name: str = '',
    service: str = '',
    capture_session=None,
    sniff_mode: str = '',
    upstream_path: str = '',
) -> Optional[int]:
    """Persist one request/response pair; return TrafficLog pk or None."""
    from dose.polysniffer.models import TrafficLog
    from dose.polysniffer.schema_patch import ensure_trafficlog_capture_columns

    tenant = getattr(request, 'tenant', None)
    _ensure_tenant_schema(tenant)
    try:
        ensure_trafficlog_capture_columns(request)
    except Exception:
        pass

    user = capture_user_in_current_schema(getattr(request, 'user', None))
    correlation_id = getattr(request, '_polysniffer_correlation_id', None) or str(uuid.uuid4())[:12]

    if capture_session is None:
        capture_session = getattr(request, '_polysniffer_capture', None) or get_active_capture_session(
            request, getattr(request, '_polysniffer_endpoint_id', None)
        )

    har_entry = build_har_entry(
        method=method,
        url=url,
        path=path or upstream_path or client_path,
        headers=headers,
        cookies=cookies,
        query_params=query_params,
        body=body,
        status_code=status_code,
        response_headers=response_headers,
        response_body=response_body,
        response_size=response_size,
        duration_ms=duration_ms,
        sniff_mode=sniff_mode,
    )

    row = TrafficLog.objects.create(
        capture_session=capture_session,
        capture_source=capture_source,
        method=method,
        url=url[:500],
        path=(path or upstream_path or client_path)[:500],
        client_path=(client_path or '')[:500],
        headers=headers or {},
        cookies=cookies or {},
        query_params=query_params or {},
        body=truncate_text(body),
        status_code=status_code,
        response_headers=response_headers or {},
        response_body=truncate_text(response_body),
        response_size=response_size or 0,
        endpoint_name=endpoint_name[:200],
        service=(service or '')[:50],
        correlation_id=correlation_id,
        user=user,
        duration_ms=round(duration_ms, 2),
        har_data={'log': {'version': '1.2', 'entries': [har_entry]}},
    )
    return row.pk


def log_django_response(
    request,
    response,
    *,
    capture_source: str,
    target_url: str,
    upstream_path: str = '',
    endpoint_name: str = '',
    service: str = '',
    sniff_mode: str = '',
    duration_ms: float = 0,
    start_time: Optional[float] = None,
) -> Optional[int]:
    if start_time is not None:
        duration_ms = (time.time() - start_time) * 1000

    try:
        req_body = request.body.decode('utf-8', errors='ignore') if request.body else ''
    except Exception:
        req_body = ''

    try:
        resp_body = response.content.decode('utf-8', errors='ignore') if hasattr(response, 'content') and response.content else ''
    except Exception:
        resp_body = ''

    resp_headers = dict(response.items()) if hasattr(response, 'items') else {}
    resp_size = len(response.content) if hasattr(response, 'content') and response.content else 0

    return log_http_exchange(
        request,
        method=request.method,
        url=target_url or request.build_absolute_uri(),
        path=upstream_path or request.path,
        client_path=(getattr(request, '_polysniffer_client_path', None) or request.path_info)[:500],
        capture_source=capture_source,
        headers=dict(request.headers),
        cookies=dict(request.COOKIES),
        query_params=dict(request.GET),
        body=req_body,
        status_code=response.status_code,
        response_headers=resp_headers,
        response_body=resp_body,
        response_size=resp_size,
        duration_ms=duration_ms,
        endpoint_name=endpoint_name,
        service=service,
        sniff_mode=sniff_mode,
        upstream_path=upstream_path,
    )


def log_requests_response(
    request,
    resp,
    *,
    capture_source: str,
    target_url: str,
    upstream_path: str = '',
    endpoint_name: str = '',
    service: str = '',
    sniff_mode: str = '',
    duration_ms: float = 0,
) -> Optional[int]:
    try:
        req_body = request.body.decode('utf-8', errors='ignore') if request.body else ''
    except Exception:
        req_body = ''

    resp_body = ''
    resp_size = 0
    try:
        resp_body = resp.content.decode('utf-8', errors='ignore') if resp.content else ''
        resp_size = len(resp.content or b'')
    except Exception:
        pass

    return log_http_exchange(
        request,
        method=request.method,
        url=target_url,
        path=upstream_path,
        client_path=(getattr(request, '_polysniffer_client_path', None) or request.path_info)[:500],
        capture_source=capture_source,
        headers=dict(getattr(request, 'headers', {})) if hasattr(request, 'headers') else {},
        cookies=dict(request.COOKIES),
        query_params=dict(request.GET),
        body=req_body,
        status_code=resp.status_code,
        response_headers=dict(resp.headers),
        response_body=resp_body,
        response_size=resp_size,
        duration_ms=duration_ms,
        endpoint_name=endpoint_name,
        service=service,
        sniff_mode=sniff_mode,
        upstream_path=upstream_path,
    )


def body_hash(text: str) -> str:
    if not text:
        return ''
    return hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest()[:16]
