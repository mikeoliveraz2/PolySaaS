"""
HubSpot OAuth — per-tenant connection (each subscriber links their own portal).
"""
from __future__ import annotations

import logging
import secrets
from datetime import timedelta
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests as http_requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

HUBSPOT_AUTH_URL = 'https://app.hubspot.com/oauth/authorize'
HUBSPOT_TOKEN_URL = 'https://api.hubapi.com/oauth/v1/token'
HUBSPOT_TOKEN_INFO_URL = 'https://api.hubapi.com/oauth/v1/access-tokens'


def hubspot_oauth_config() -> Dict[str, str]:
    redirect = getattr(settings, 'HUBSPOT_REDIRECT_URI', '') or ''
    if not redirect:
        site = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
        redirect = f'{site}/dose/hubspot/oauth/callback/'
    return {
        'client_id': getattr(settings, 'HUBSPOT_CLIENT_ID', ''),
        'client_secret': getattr(settings, 'HUBSPOT_CLIENT_SECRET', ''),
        'redirect_uri': redirect,
        'scopes': getattr(
            settings,
            'HUBSPOT_SCOPES',
            'crm.objects.contacts.read crm.objects.companies.read crm.objects.deals.read tickets',
        ),
    }


def build_authorization_url(*, state: str) -> str:
    cfg = hubspot_oauth_config()
    params = {
        'client_id': cfg['client_id'],
        'redirect_uri': cfg['redirect_uri'],
        'scope': cfg['scopes'],
        'state': state,
    }
    return f'{HUBSPOT_AUTH_URL}?{urlencode(params)}'


def generate_oauth_state() -> str:
    return secrets.token_urlsafe(32)


def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    cfg = hubspot_oauth_config()
    resp = http_requests.post(
        HUBSPOT_TOKEN_URL,
        data={
            'grant_type': 'authorization_code',
            'client_id': cfg['client_id'],
            'client_secret': cfg['client_secret'],
            'redirect_uri': cfg['redirect_uri'],
            'code': code,
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=30,
    )
    if not resp.ok:
        logger.warning('[HubSpotOAuth] token exchange failed: %s %s', resp.status_code, resp.text[:300])
        return {'ok': False, 'error': resp.text[:500], 'status_code': resp.status_code}
    data = resp.json()
    return {'ok': True, **data}


def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    cfg = hubspot_oauth_config()
    resp = http_requests.post(
        HUBSPOT_TOKEN_URL,
        data={
            'grant_type': 'refresh_token',
            'client_id': cfg['client_id'],
            'client_secret': cfg['client_secret'],
            'refresh_token': refresh_token,
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=30,
    )
    if not resp.ok:
        logger.warning('[HubSpotOAuth] refresh failed: %s %s', resp.status_code, resp.text[:300])
        return {'ok': False, 'error': resp.text[:500], 'status_code': resp.status_code}
    return {'ok': True, **resp.json()}


def fetch_token_metadata(access_token: str) -> Dict[str, Any]:
    try:
        resp = http_requests.get(
            f'{HUBSPOT_TOKEN_INFO_URL}/{access_token}',
            timeout=15,
        )
        if resp.ok:
            return resp.json()
    except Exception as exc:
        logger.warning('[HubSpotOAuth] token metadata failed: %s', exc)
    return {}


def persist_tokens_on_tenant_app(tenant_app, token_payload: Dict[str, Any]) -> None:
    """Merge OAuth tokens into TenantApp.extra_config."""
    extra = tenant_app.extra_config if isinstance(tenant_app.extra_config, dict) else {}
    access = token_payload.get('access_token', '')
    refresh = token_payload.get('refresh_token', extra.get('hs_refresh_token', ''))
    expires_in = int(token_payload.get('expires_in') or 0)
    expires_at = ''
    if expires_in > 0:
        expires_at = (timezone.now() + timedelta(seconds=expires_in)).isoformat()

    meta = fetch_token_metadata(access) if access else {}
    portal_id = str(meta.get('hub_id') or meta.get('hubId') or extra.get('hs_portal_id') or '')
    user_id = str(meta.get('user_id') or meta.get('userId') or '')

    extra.update({
        'hs_access_token': access,
        'hs_refresh_token': refresh,
        'hs_token_expires_at': expires_at,
        'hs_portal_id': portal_id,
        'hs_user_id': user_id,
    })
    tenant_app.extra_config = extra
    tenant_app.save(update_fields=['extra_config'])


def get_tenant_hubspot_app(tenant):
    from dose.models import TenantApp

    return TenantApp.public_bundles.filter(tenant=tenant, app_name='hubspot').first()


def tenant_has_hubspot_connection(tenant) -> bool:
    ta = get_tenant_hubspot_app(tenant)
    if not ta or not isinstance(ta.extra_config, dict):
        return False
    return bool(ta.extra_config.get('hs_access_token'))
