#!/usr/bin/env python
"""
Provision Mattermost for a specific tenant NOW.
Run this after MATTERMOST_ADMIN_TOKEN is set.
Usage: python provision_mattermost_now.py <tenant_slug>
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from dose.services.mattermost_tenant_provisioner import provision_mattermost_tenant
from dose.models import Tenant, TenantApp
from django.db import connection

def main(tenant_slug):
    with connection.cursor() as cur:
        cur.execute('SET search_path TO public')

    try:
        t = Tenant.objects.get(slug=tenant_slug)
    except Tenant.DoesNotExist:
        print(f"ERROR: Tenant '{tenant_slug}' not found")
        return 1

    print(f"Tenant: {t.name} (schema: {t.schema_name})")

    # Find admin user
    admin_member = t.memberships.filter(role='admin').first() or t.memberships.first()
    if not admin_member:
        print("ERROR: No members found for this tenant")
        return 1

    admin_email = admin_member.user.email
    admin_username = admin_email.split('@')[0].lower() if '@' in admin_email else tenant_slug
    print(f"Admin: {admin_email} (username: {admin_username})")

    # Find or create TenantApp
    ta = TenantApp.objects.filter(tenant=t, app_name='mattermost').first()
    tenant_app_id = ta.id if ta else None

    if ta:
        print(f"Existing TenantApp status: {ta.status}")
        cfg = ta.extra_config or {}
        print(f"Current login_id: {cfg.get('mattermost_login_id') or cfg.get('mm_login_id') or '(missing)'}")

    # Provision
    print("\nProvisioning Mattermost...")
    result = provision_mattermost_tenant(
        tenant_schema=t.schema_name,
        tenant_name=t.name,
        admin_email=admin_email,
        company_name=t.name,
        tenant_app_id=tenant_app_id,
        admin_username=admin_username,
        admin_password='',  # Will auto-generate strong password
    )

    print(f"\nResult: {'SUCCESS' if result.get('success') else 'FAILED'}")
    if result.get('error'):
        print(f"Error: {result['error']}")
    print(f"Details: {result}")
    return 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python provision_mattermost_now.py <tenant_slug>")
        print("Example: python provision_mattermost_now.py polysaase2e2")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
