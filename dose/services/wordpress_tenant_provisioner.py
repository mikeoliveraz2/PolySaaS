"""
WordPress CMS tenant provisioner.
Creates PassThroughEndpoint for WordPress on tenant subscription.
"""
from typing import Dict, Any
from django.db import connection
from celery import shared_task
from dose.models import PassThroughEndpoint

WORDPRESS_API_BASE = "http://localhost:8085"  # Local Docker service


@shared_task
def provision_wordpress_tenant(
    tenant_schema: str,
    tenant_name: str,
    admin_email: str,
    company_name: str,
    oauth_client_id: str = '',
    oauth_client_secret: str = '',
    tenant_app_id: int = None,
) -> Dict[str, Any]:
    """
    Atomic Service: Create WordPress PassThroughEndpoint on new subscription
    Triggered when "WordPress" is checked on subscribe form
    """
    # 1. Set tenant schema for PassThroughEndpoint creation
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{tenant_schema}"')

    # 2. Create PassThroughEndpoint for WordPress
    wordpress_endpoint, _created = PassThroughEndpoint.objects.update_or_create(
        trigger_path='wordpress',
        defaults={
            'endpoint_url': WORDPRESS_API_BASE,
            'description': 'WordPress CMS - tenant-specific instance',
            'is_enabled': True,
            'passthrough_type': 'scraper',
            'integration_mode': 'web_api',
            'api_endpoint': f"{WORDPRESS_API_BASE}/wp-json/wp/v2",
            'show_in_menu': True,
            'menu_title': 'WordPress',
            'menu_icon': 'wordpress',
            'menu_sort_order': 60,
            'starting_uri': '/wp-admin',
        }
    )
    print(f"Created PassThroughEndpoint for WordPress: {wordpress_endpoint.trigger_path} -> {wordpress_endpoint.endpoint_url}")

    return {
        "success": True,
        "wordpress_url": WORDPRESS_API_BASE,
        "wordpress_credentials": {
            "username": "admin",
            "password": "admin",
            "note": "Default WordPress admin credentials"
        },
        "message": "WordPress tenant provisioned successfully"
    }
