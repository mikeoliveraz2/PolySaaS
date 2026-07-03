"""
HubSpot tenant provisioner — PassThroughEndpoint + TenantApp (OAuth completed separately).
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from celery import shared_task
from django.conf import settings
from django.db import connection

from dose.models import PassThroughEndpoint, TenantApp
from dose.services.oauth2_registration import mark_tenant_app_active, mark_tenant_app_error

logger = logging.getLogger(__name__)

HUBSPOT_APP_URL = getattr(settings, 'HUBSPOT_APP_URL', 'https://app.hubspot.com')


def _hubspot_endpoint_defaults(company_name: str) -> Dict[str, Any]:
    return {
        'endpoint_url': HUBSPOT_APP_URL,
        'description': f'HubSpot CRM for {company_name}',
        'is_enabled': True,
        'passthrough_type': 'scraper',
        'integration_mode': 'web_api',
        'api_endpoint': 'https://api.hubapi.com',
        'show_in_menu': True,
        'menu_title': 'HubSpot',
        'menu_icon': 'hubspot',
        'menu_sort_order': 35,
        'starting_uri': '/login/',
    }


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def provision_hubspot_tenant(
    self,
    tenant_schema: str,
    tenant_name: str,
    admin_email: str,
    company_name: str,
    oauth_client_id: str = '',
    oauth_client_secret: str = '',
    tenant_app_id: int = None,
) -> Dict[str, Any]:
    """
    Ensure HubSpot PassThroughEndpoint and TenantApp exist.
    OAuth connect (/dose/hubspot/oauth/start/) marks the app active when tokens are stored.
    """
    tenant_app = None
    if tenant_app_id:
        try:
            tenant_app = TenantApp.objects.get(id=tenant_app_id)
        except TenantApp.DoesNotExist:
            logger.warning('[HubSpotProvisioner] TenantApp id=%s not found', tenant_app_id)

    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{tenant_schema}", public')

        PassThroughEndpoint.objects.update_or_create(
            slug='hubspot',
            defaults=_hubspot_endpoint_defaults(company_name or tenant_name),
        )
        logger.info('[HubSpotProvisioner] PassThroughEndpoint ensured for %s', tenant_schema)
    except Exception as exc:
        logger.exception('[HubSpotProvisioner] PassThroughEndpoint failed: %s', exc)
        if tenant_app:
            mark_tenant_app_error(tenant_app, str(exc))
        return {'success': False, 'error': str(exc)}

    if tenant_app:
        try:
            extra = tenant_app.extra_config if isinstance(tenant_app.extra_config, dict) else {}
            extra.setdefault('hs_connect_hint', 'Visit /dose/hubspot/oauth/start/ to link your HubSpot portal')
            extra.setdefault('hs_oauth_connected', bool(extra.get('hs_access_token')))
            tenant_app.extra_config = extra
            tenant_app.save(update_fields=['extra_config'])
            # Mark HubSpot app active once endpoint scaffolding is ready so subscribe
            # treats it like other bundled apps (OAuth still required for API features).
            mark_tenant_app_active(tenant_app)
        except Exception as exc:
            logger.warning('[HubSpotProvisioner] TenantApp update failed: %s', exc)

    return {
        'success': True,
        'schema': tenant_schema,
        'oauth_required': True,
        'connect_path': '/dose/hubspot/oauth/start/',
        'message': 'HubSpot passthrough endpoint created. Connect OAuth to enable API portlets.',
    }
