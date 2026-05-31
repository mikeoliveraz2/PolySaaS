#!/usr/bin/env python
"""
Quick test: Subscribe t104 and verify Odoo provisioning.
This simulates the subscription flow without Stripe for testing.
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.db import transaction
from django.contrib.auth import get_user_model
from dose.models import Tenant, UserProfile, UserTenantMembership, Subscription
from dose.services.odoo_tenant_provisioner import provision_odoo_tenant
from dose.services.mattermost_tenant_provisioner import provision_mattermost_tenant

User = get_user_model()


def test_subscribe_t104():
    """Create t104 tenant and trigger provisioning."""
    
    tenant_name = "PolySaaS Test 104"
    tenant_slug = "t104"
    admin_email = "admin104@example.com"
    admin_password = "TestPass123!"
    
    print("=" * 60)
    print(f"TEST SUBSCRIBE: {tenant_name} ({tenant_slug})")
    print("=" * 60)
    
    # Check if tenant exists
    existing = Tenant.objects.filter(schema_name=tenant_slug).first()
    if existing:
        print(f"⚠ Tenant {tenant_slug} already exists, skipping creation")
        tenant = existing
    else:
        # Create tenant
        print(f"Creating tenant: {tenant_name}...")
        tenant = Tenant.objects.create(
            name=tenant_name,
            schema_name=tenant_slug,
            description="Test tenant t104 for Odoo provisioning verification",
        )
        print(f"✓ Tenant created: {tenant.schema_name}")
        
        # Run migrations in the configured default DB (no schema_name option here)
        from django.core.management import call_command
        call_command('migrate', run_syncdb=True, verbosity=0)
        print("✓ Migrations completed")
    
    # Check if user exists
    user = User.objects.filter(email=admin_email).first()
    if user:
        print(f"⚠ User {admin_email} already exists")
    else:
        # Create admin user
        print(f"Creating admin user: {admin_email}...")
        user = User.objects.create_user(
            username=admin_email.split('@')[0],
            email=admin_email,
            password=admin_password,
            first_name="Admin",
            last_name="104",
        )
        print(f"✓ User created: {user.email}")
    
    # Create UserProfile
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={'phone': '', 'bio': ''}
    )
    
    # Create UserTenantMembership
    membership, created = UserTenantMembership.objects.get_or_create(
        user=user,
        tenant=tenant,
        defaults={'role': UserTenantMembership.Role.OWNER}
    )
    if created:
        print(f"✓ Membership created: {user.email} -> {tenant.schema_name} (Owner)")
    
    # Create Subscription
    sub, _ = Subscription.objects.get_or_create(
        tenant=tenant,
        defaults={
            'plan_tier': 'polysaas-1',
            'active': True,
            'stripe_customer_id': 'test_cus_t104',
            'stripe_subscription_id': 'test_sub_t104',
        }
    )
    print(f"✓ Subscription: {sub.plan_tier} (Active: {sub.active})")
    
    # Create TenantApps for bundled apps
    from dose.models import TenantApp
    
    apps_to_enable = ['odoo', 'mattermost']  # Test Odoo and Mattermost
    
    for app_name in apps_to_enable:
        ta, created = TenantApp.objects.get_or_create(
            tenant=tenant,
            app_name=app_name,
            defaults={
                'status': 'pending',
                'app_url': '',
            }
        )
        if created:
            print(f"✓ TenantApp created: {app_name} (status: {ta.status})")
        else:
            print(f"⚠ TenantApp exists: {app_name} (status: {ta.status})")
    
    print("\n" + "=" * 60)
    print("TRIGGERING PROVISIONING")
    print("=" * 60)
    
    # Trigger Odoo provisioning
    print(f"\n1. Odoo Provisioning...")
    odoo_result = provision_odoo_tenant(
        tenant_schema=tenant.schema_name,
        tenant_name=tenant.name,
        admin_email=user.email,
        company_name=tenant.name,
        tenant_app_id=TenantApp.objects.get(tenant=tenant, app_name='odoo').id,
    )
    
    print(f"   Result: success={odoo_result.get('success')}")
    print(f"   Message: {odoo_result.get('message')}")
    print(f"   Odoo User ID: {odoo_result.get('odoo_user_id')}")
    
    if not odoo_result.get('success'):
        print(f"   ERROR: {odoo_result.get('error')}")
    
    # Trigger Mattermost provisioning
    print(f"\n2. Mattermost Provisioning...")
    mm_result = provision_mattermost_tenant(
        tenant_schema=tenant.schema_name,
        tenant_name=tenant.name,
        admin_email=user.email,
        company_name=tenant.name,
        admin_username=user.email.split('@')[0],
        admin_password=admin_password,
        tenant_app_id=TenantApp.objects.get(tenant=tenant, app_name='mattermost').id,
    )
    
    print(f"   Result: success={mm_result.get('success')}")
    print(f"   Message: {mm_result.get('message')}")
    print(f"   Team ID: {mm_result.get('team_id')}")
    print(f"   User ID: {mm_result.get('mm_user_id')}")
    
    if not mm_result.get('success'):
        print(f"   ERROR: {mm_result.get('error')}")
    
    # Final status
    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)
    
    # Check TenantApp statuses
    for ta in TenantApp.objects.filter(tenant=tenant):
        icon = "✅" if ta.status == 'active' else "❌"
        print(f"   {icon} {ta.app_name}: {ta.status}")
    
    # Verify Odoo user exists
    print(f"\n3. Verifying Odoo user exists...")
    from check_odoo_user import check_odoo_user
    odoo_exists = check_odoo_user(user.email)
    
    if odoo_result.get('success') and odoo_exists:
        print("\n✅ SUCCESS: Odoo provisioning working correctly!")
    elif odoo_result.get('success') and not odoo_exists:
        print("\n❌ MISMATCH: Provisioner reported success but user doesn't exist!")
    else:
        print(f"\n❌ FAILED: Odoo provisioning failed - {odoo_result.get('error')}")
    
    print("\n" + "=" * 60)
    print(f"Login: {admin_email}")
    print(f"Password: {admin_password}")
    print(f"Tenant: {tenant_slug}")
    print("=" * 60)


if __name__ == '__main__':
    test_subscribe_t104()
