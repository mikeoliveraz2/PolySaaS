#!/usr/bin/env python
"""
Manual Odoo Provisioning Test Script for PolySaaS Tenant
Usage: python test_manual_odoo_provision.py <tenant_slug> <admin_email>
Example: python test_manual_odoo_provision.py polysaast113 polysaast113@you.com
"""
import sys
import django
import os

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from dose.models import Tenant, TenantApp, PassThroughEndpoint
from dose.services.odoo_tenant_provisioner import _get_odoo_shared_config, _odoo_authenticate, _odoo_create_user
from dose.services.oauth2_registration import mark_tenant_app_active
from django.db import connection

if len(sys.argv) < 3:
    print("Usage: python test_manual_odoo_provision.py <tenant_slug> <admin_email>")
    sys.exit(1)

tenant_slug = sys.argv[1]
admin_email = sys.argv[2]

print(f"[INFO] Attempting Odoo provisioning for tenant: {tenant_slug}, admin: {admin_email}")

tenant = Tenant.objects.filter(slug=tenant_slug).first()
if not tenant:
    print(f"[ERROR] Tenant not found: {tenant_slug}")
    sys.exit(1)

company_name = tenant.name

# Create or get the Odoo TenantApp
tenant_app, _ = TenantApp.objects.get_or_create(
    tenant=tenant,
    app_name='odoo',
    defaults={
        'status': 'provisioning',
        'extra_config': {},
    }
)

try:
    config = _get_odoo_shared_config()
    odoo_url = config['url']
    password = config['admin_password']
    # Step 1: Create PassThroughEndpoint
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{tenant.schema_name}", public')
    PassThroughEndpoint.objects.update_or_create(
        slug='odoo',
        defaults={
            'endpoint_url': odoo_url,
            'description': f'Odoo ERP for {company_name or tenant_slug}',
            'is_enabled': True,
            'passthrough_type': 'scraper',
            'integration_mode': 'web_api',
            'api_endpoint': f"{odoo_url}/web",
            'show_in_menu': True,
            'menu_title': 'Odoo',
            'menu_icon': 'building',
            'menu_sort_order': 20,
            'starting_uri': '/web',
        }
    )
    print("[INFO] PassThroughEndpoint ensured.")
    # Step 2: Create Odoo user
    uid = _odoo_authenticate(config)
    odoo_user_id = _odoo_create_user(
        config, uid,
        login=admin_email,
        name=company_name or tenant_slug,
        password=password,
    )
    print(f"[INFO] Odoo user created with id: {odoo_user_id}")
    # Step 3: Update TenantApp
    extra = tenant_app.extra_config if isinstance(tenant_app.extra_config, dict) else {}
    extra.update({
        'odoo_login': admin_email,
        'odoo_password': password,
        'odoo_db': config['db'],
        'odoo_user_id': odoo_user_id,
        'odoo_url': odoo_url,
    })
    tenant_app.extra_config = extra
    tenant_app.status = 'active'
    tenant_app.save(update_fields=['extra_config', 'status'])
    mark_tenant_app_active(tenant_app, app_url=odoo_url)
    print("[SUCCESS] Odoo provisioning complete!")
except Exception as e:
    print(f"[ERROR] Odoo provisioning failed: {e}")
    import traceback
    traceback.print_exc()
    tenant_app.status = 'error'
    tenant_app.last_error = str(e)
    tenant_app.save(update_fields=['status', 'last_error'])
    sys.exit(1)
