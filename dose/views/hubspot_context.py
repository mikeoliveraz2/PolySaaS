"""
HubSpot User Context Manager views + OAuth routes.
"""
from __future__ import annotations

import json
import logging

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from dose.services.hubspot_oauth import (
    build_authorization_url,
    exchange_code_for_tokens,
    generate_oauth_state,
    get_tenant_hubspot_app,
    persist_tokens_on_tenant_app,
    tenant_has_hubspot_connection,
)
from dose.services.hubspot_portlet_services import load_portlet_by_slug
from dose.services.oauth2_registration import mark_tenant_app_active
from dose.utils import get_current_tenant

logger = logging.getLogger(__name__)

DEFAULT_PORTLETS = (
    ('contacts', 'Contacts', 'HubSpotContactsPortlet', '👤', 10),
    ('companies', 'Companies', 'HubSpotCompaniesPortlet', '🏢', 20),
    ('deals', 'Deals', 'HubSpotDealsPortlet', '💼', 30),
    ('tickets', 'Tickets', 'HubSpotTicketsPortlet', '🎫', 40),
    ('tasks', 'Tasks', 'HubSpotTasksPortlet', '✅', 50),
)


def _ensure_tenant_schema(tenant):
    if tenant and getattr(tenant, 'schema_name', None):
        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{tenant.schema_name}", public')


def _seed_portlet_definitions(tenant):
    from dose.models import HubSpotPortletDefinition

    _ensure_tenant_schema(tenant)
    for slug, title, script, icon, order in DEFAULT_PORTLETS:
        HubSpotPortletDefinition.objects.update_or_create(
            tenant=tenant,
            slug=slug,
            defaults={
                'title': title,
                'executescript': script,
                'hubspot_object_type': slug,
                'icon': icon,
                'default_sort_order': order,
                'is_active': True,
            },
        )


def _ensure_user_portlets(user, tenant):
    from dose.models import HubSpotPortletDefinition, UserHubSpotPortlet

    _seed_portlet_definitions(tenant)
    defs = list(HubSpotPortletDefinition.objects.filter(tenant=tenant, is_active=True))
    existing = set(
        UserHubSpotPortlet.objects.filter(user=user, tenant=tenant).values_list('definition_id', flat=True)
    )
    for d in defs:
        if d.id in existing:
            continue
        UserHubSpotPortlet.objects.create(
            tenant=tenant,
            user=user,
            definition=d,
            sort_order=d.default_sort_order,
            is_visible=True,
            column_span=1,
        )


@login_required
@require_GET
def hubspot_user_context_view(request):
    tenant = get_current_tenant(request)
    if not tenant:
        return render(request, 'dose/hubspot_user_context.html', {
            'error': 'No tenant context. Select a tenant first.',
            'portlets': [],
            'connected': False,
        })
    _ensure_user_portlets(request.user, tenant)
    from dose.models import UserHubSpotPortlet

    _ensure_tenant_schema(tenant)
    rows = (
        UserHubSpotPortlet.objects.filter(user=request.user, tenant=tenant, is_visible=True)
        .select_related('definition')
        .order_by('sort_order', 'id')
    )
    portlets = [
        {
            'slug': r.definition.slug,
            'title': r.definition.title,
            'icon': r.definition.icon,
            'sort_order': r.sort_order,
            'column_span': r.column_span,
        }
        for r in rows
    ]
    return render(request, 'dose/hubspot_user_context.html', {
        'portlets': portlets,
        'connected': tenant_has_hubspot_connection(tenant),
        'connect_url': reverse('dose:hubspot_oauth_start'),
        'passthrough_url': '/pt/admin/app.hubspot.com/contacts/',
    })


@login_required
@require_GET
def hubspot_portlet_data_api(request, slug):
    tenant = get_current_tenant(request)
    if not tenant:
        return JsonResponse({'status': 'error', 'error': 'no tenant'}, status=400)
    limit = int(request.GET.get('limit') or 10)
    payload = load_portlet_by_slug(request, slug, limit=limit)
    code = 200 if payload.get('status') == 'success' else 400
    return JsonResponse(payload, status=code)


@login_required
@require_POST
def hubspot_portlet_layout_api(request):
    tenant = get_current_tenant(request)
    if not tenant:
        return JsonResponse({'status': 'error', 'error': 'no tenant'}, status=400)
    try:
        body = json.loads(request.body.decode('utf-8') if request.body else '{}')
    except json.JSONDecodeError:
        return HttpResponseBadRequest('invalid json')

    order = body.get('order') or []
    visibility = body.get('visibility') or {}

    from dose.models import HubSpotPortletDefinition, UserHubSpotPortlet

    _ensure_tenant_schema(tenant)
    _ensure_user_portlets(request.user, tenant)

    for idx, slug in enumerate(order):
        try:
            defn = HubSpotPortletDefinition.objects.get(tenant=tenant, slug=slug)
        except HubSpotPortletDefinition.DoesNotExist:
            continue
        UserHubSpotPortlet.objects.update_or_create(
            tenant=tenant,
            user=request.user,
            definition=defn,
            defaults={
                'sort_order': (idx + 1) * 10,
                'is_visible': bool(visibility.get(slug, True)),
            },
        )
    return JsonResponse({'status': 'ok'})


@login_required
@require_GET
def hubspot_oauth_start(request):
    tenant = get_current_tenant(request)
    if not tenant:
        return HttpResponseBadRequest('No tenant context')
    state = generate_oauth_state()
    request.session['hubspot_oauth_state'] = state
    request.session['hubspot_oauth_tenant'] = getattr(tenant, 'slug', None) or str(tenant.pk)
    request.session.modified = True
    return HttpResponseRedirect(build_authorization_url(state=state))


@login_required
@require_GET
def hubspot_oauth_callback(request):
    err = request.GET.get('error')
    if err:
        return render(request, 'dose/hubspot_connect.html', {
            'error': err,
            'detail': request.GET.get('error_description', ''),
        })
    code = request.GET.get('code')
    state = request.GET.get('state')
    expected = request.session.get('hubspot_oauth_state')
    if not code or not state or state != expected:
        return HttpResponseBadRequest('Invalid OAuth state')

    tenant_slug_saved = request.session.pop('hubspot_oauth_tenant', None)
    request.session.pop('hubspot_oauth_state', None)
    tenant = get_current_tenant(request)
    if not tenant and tenant_slug_saved:
        from dose.models import Tenant
        tenant = Tenant.objects.filter(slug=tenant_slug_saved).first()

    token_result = exchange_code_for_tokens(code)
    if not token_result.get('ok'):
        return render(request, 'dose/hubspot_connect.html', {
            'error': 'token_exchange_failed',
            'detail': token_result.get('error', ''),
        })

    ta = get_tenant_hubspot_app(tenant)
    if not ta:
        return render(request, 'dose/hubspot_connect.html', {
            'error': 'hubspot_not_enabled',
            'detail': 'Enable HubSpot for this tenant first.',
        })

    persist_tokens_on_tenant_app(ta, token_result)
    mark_tenant_app_active(ta)
    _seed_portlet_definitions(tenant)

    return HttpResponseRedirect(reverse('dose:hubspot_user_context'))
