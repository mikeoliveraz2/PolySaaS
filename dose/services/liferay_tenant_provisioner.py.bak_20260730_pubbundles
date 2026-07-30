"""
Liferay Portal tenant provisioner.
Creates PassThroughEndpoint for Liferay on tenant subscription.
"""
from typing import Dict, Any
from django.db import connection
from celery import shared_task
from dose.models import PassThroughEndpoint

LIFERAY_API_BASE = "http://localhost:8084"  # Local Docker service


@shared_task
def provision_liferay_tenant(
    tenant_schema: str,
    tenant_name: str,
    admin_email: str,
    company_name: str,
    oauth_client_id: str = '',
    oauth_client_secret: str = '',
    tenant_app_id: int = None,
) -> Dict[str, Any]:
    """
    Atomic Service: Create Liferay PassThroughEndpoint on new subscription
    Triggered when "Liferay" is checked on subscribe form
    """
    # 1. Set tenant schema for PassThroughEndpoint creation
    from django.conf import settings
    password = getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!')
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{tenant_schema}"')

    # 2. Create PassThroughEndpoint for Liferay
    liferay_endpoint, _created = PassThroughEndpoint.objects.update_or_create(
        trigger_path='liferay',
        defaults={
            'endpoint_url': LIFERAY_API_BASE,
            'description': 'Liferay Portal - tenant-specific instance',
            'is_enabled': True,
            'passthrough_type': 'scraper',
            'integration_mode': 'web_api',
            'api_endpoint': f"{LIFERAY_API_BASE}/api/jsonws",
            'show_in_menu': True,
            'menu_title': 'Liferay',
            'menu_icon': 'landmark',
            'menu_sort_order': 50,
            'starting_uri': '/web/guest',
        }
    )
    print(f"Created PassThroughEndpoint for Liferay: {liferay_endpoint.trigger_path} -> {liferay_endpoint.endpoint_url}")

    return {
        "success": True,
        "liferay_url": LIFERAY_API_BASE,
        "liferay_credentials": {
            "username": "liferayAdmin",
            "password": password,
            "note": "Standard app-admin credentials"
        },
        "message": "Liferay tenant provisioned successfully"
    }
