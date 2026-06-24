"""
PolySniffer 2.0 — dual-mode sniff views (native + passthrough).
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24
from __future__ import annotations

import json
import re
from urllib.parse import urlparse

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from dose.polysniffer.gcs_export import export_har_to_gcs
from dose.polysniffer.har_capture import body_hash, get_active_capture_session
from dose.polysniffer.models import TrafficCapture, TrafficLog
from dose.polysniffer.schema_patch import ensure_trafficlog_capture_columns
from dose.polysniffer.sniff_forward import forward_sniff_native
from dose.polysniffer.views.core import get_endpoint_any_schema
from dose.utils import get_current_tenant


def _endpoint_trigger(endpoint) -> str:
    raw = (endpoint.endpoint_url or '').strip()
    if raw.startswith('http://') or raw.startswith('https://'):
        return urlparse(raw).netloc
    return raw.split('/')[0]


def _session_name(endpoint_id: int, mode: str) -> str:
    ts = timezone.now().strftime('%Y%m%d-%H%M')
    safe_mode = mode if mode in ('native', 'passthrough', 'workspace') else 'workspace'
    return f'ep{endpoint_id}-{safe_mode}-{ts}'


@staff_member_required
def mode_picker(request, endpoint_id: int):
    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception as exc:
        return HttpResponse(f'Endpoint not found: {exc}', status=404)

    tenant = get_current_tenant(request)
    active = get_active_capture_session(request, endpoint_id)
    context = {
        'endpoint': endpoint,
        'endpoint_id': endpoint_id,
        'active_session': active,
        'native_url': f'/dose/sniff/{endpoint_id}/native/',
        'passthrough_url': f'/dose/sniff/{endpoint_id}/passthrough/',
        'diff_url': f'/dose/sniff/{endpoint_id}/diff/',
        'export_url': f'/dose/sniff/{endpoint_id}/export-har/',
    }
    return render(request, 'polysniffer/mode_picker.html', context)


@staff_member_required
@require_http_methods(['POST'])
def session_start(request, endpoint_id: int):
    mode = (request.POST.get('mode') or 'native').strip().lower()
    if mode not in ('native', 'passthrough'):
        return JsonResponse({'error': 'mode must be native or passthrough'}, status=400)

    tenant = get_current_tenant(request)
    if not tenant:
        return JsonResponse({'error': 'no tenant context'}, status=400)

    TrafficCapture.objects.filter(tenant=tenant, is_active=True).update(is_active=False)
    cap = TrafficCapture.objects.create(
        tenant=tenant,
        capture_name=_session_name(endpoint_id, mode),
        description=f'PolySniffer 2.0 {mode} endpoint_id={endpoint_id}',
        is_active=True,
    )
    request.session[f'polysniffer_ep{endpoint_id}_mode'] = mode
    return JsonResponse({
        'ok': True,
        'capture_id': cap.id,
        'capture_name': cap.capture_name,
        'mode': mode,
    })


@staff_member_required
@require_http_methods(['POST'])
def session_stop(request, endpoint_id: int):
    tenant = get_current_tenant(request)
    if not tenant:
        return JsonResponse({'error': 'no tenant context'}, status=400)
    updated = TrafficCapture.objects.filter(tenant=tenant, is_active=True).update(is_active=False)
    return JsonResponse({'ok': True, 'stopped': updated})


@staff_member_required
@csrf_exempt
def native_sniff_proxy(request, endpoint_id: int, path: str = ''):
    if not request.user.is_staff:
        return HttpResponseForbidden('Staff only')
    endpoint = get_endpoint_any_schema(endpoint_id, request)
    request._polysniffer_endpoint_id = endpoint_id
    request._polysniffer_sniff_mode = 'native'
    cap = get_active_capture_session(request, endpoint_id)
    if cap:
        request._polysniffer_capture = cap
    return forward_sniff_native(request, endpoint, path)


@staff_member_required
@csrf_exempt
def passthrough_sniff_proxy(request, endpoint_id: int, path: str = ''):
    if not request.user.is_staff:
        return HttpResponseForbidden('Staff only')
    endpoint = get_endpoint_any_schema(endpoint_id, request)
    request._polysniffer_endpoint_id = endpoint_id
    request._polysniffer_sniff_mode = 'passthrough'
    cap = get_active_capture_session(request, endpoint_id)
    if cap:
        request._polysniffer_capture = cap

    trigger = _endpoint_trigger(endpoint)
    subpath = path or ''
    if subpath and not subpath.startswith('/'):
        subpath = '/' + subpath

    # Dispatch through production passthrough view (handlers + orchestration).
    from dose.admin_views import pt_admin_generic_passthrough_view

    sniff_prefix = f'/dose/sniff/{endpoint_id}/passthrough'
    pt_path = f'/pt/admin/{trigger}{subpath}'
    request.path_info = pt_path
    request.path = pt_path
    request.META['PATH_INFO'] = pt_path
    request._polysniffer_client_path = f'{sniff_prefix}{subpath or "/"}'

    return pt_admin_generic_passthrough_view(request, endpoint=trigger, subpath=subpath.lstrip('/') or None)


@staff_member_required
def sniff_diff(request, endpoint_id: int):
    ensure_trafficlog_capture_columns(request)
    tenant = get_current_tenant(request)
    session = get_active_capture_session(request, endpoint_id)
    if not session and tenant:
        prefix = f'ep{endpoint_id}-'
        session = (
            TrafficCapture.objects.filter(tenant=tenant, capture_name__startswith=prefix)
            .order_by('-created_at')
            .first()
        )

    qs = TrafficLog.objects.all()
    if session:
        qs = qs.filter(capture_session=session)
    else:
        qs = qs.filter(endpoint_name__icontains=str(endpoint_id))[:200]

    native_rows = { _norm_path(r.path): r for r in qs.filter(capture_source=TrafficLog.CAPTURE_NATIVE) }
    pt_rows = { _norm_path(r.path): r for r in qs.filter(capture_source=TrafficLog.CAPTURE_PASSTHROUGH) }

    diffs = []
    all_paths = sorted(set(native_rows) | set(pt_rows))
    for p in all_paths:
        n = native_rows.get(p)
        t = pt_rows.get(p)
        if not n or not t:
            diffs.append({'path': p, 'status': 'missing_side', 'native': bool(n), 'passthrough': bool(t)})
            continue
        mismatches = []
        if n.status_code != t.status_code:
            mismatches.append(f'status {n.status_code} vs {t.status_code}')
        if body_hash(n.response_body) != body_hash(t.response_body):
            mismatches.append('response body hash differs')
        if n.method != t.method:
            mismatches.append(f'method {n.method} vs {t.method}')
        if mismatches:
            diffs.append({'path': p, 'status': 'mismatch', 'issues': mismatches, 'native_id': n.id, 'pt_id': t.id})
        else:
            diffs.append({'path': p, 'status': 'match'})

    return render(request, 'polysniffer/diff_view.html', {
        'endpoint_id': endpoint_id,
        'session': session,
        'diffs': diffs,
        'mismatch_count': sum(1 for d in diffs if d.get('status') == 'mismatch'),
    })


def _norm_path(path: str) -> str:
    p = (path or '/').split('?')[0]
    return p.rstrip('/') or '/'


@staff_member_required
def export_session_har(request, endpoint_id: int):
    ensure_trafficlog_capture_columns(request)
    session = get_active_capture_session(request, endpoint_id)
    tenant = get_current_tenant(request)
    if not session and tenant:
        prefix = f'ep{endpoint_id}-'
        session = (
            TrafficCapture.objects.filter(tenant=tenant, capture_name__startswith=prefix)
            .order_by('-created_at')
            .first()
        )

    qs = TrafficLog.objects.order_by('captured_at')
    if session:
        qs = qs.filter(capture_session=session)
    else:
        qs = qs.filter(client_path__contains=f'/sniff/{endpoint_id}/')[:500]

    entries = []
    for log in qs:
        if log.har_data and log.har_data.get('log', {}).get('entries'):
            entries.extend(log.har_data['log']['entries'])
        else:
            entries.append(log.to_har_entry())

    har = {'log': {'version': '1.2', 'creator': {'name': 'PolySniffer', 'version': '2.0'}, 'entries': entries}}

    if request.GET.get('gcs') == '1' and tenant and session:
        uri = export_har_to_gcs(har, tenant_slug=tenant.schema_name, capture_id=session.id)
        if uri:
            return JsonResponse({'ok': True, 'gcs_uri': uri})

    response = HttpResponse(json.dumps(har, indent=2), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="polysniffer-ep{endpoint_id}.har"'
    return response
