#!/usr/bin/env python
"""Provision Mattermost for tenant t27 and validate login works end-to-end."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django
django.setup()

import requests
from django.db import connection
from dose.models import Tenant, TenantApp
from dose.services.mattermost_tenant_provisioner import provision_mattermost_tenant

print("="*60)
print("T27 MATTERMOST PROVISIONING & VALIDATION")
print("="*60)

# Step 1: Get or create tenant t27
tenant_slug = 'polysaast27'
tenant_name = 'PolySaaS Test 27'
schema_name = 'polysaast27'

t, created = Tenant.objects.get_or_create(
    slug=tenant_slug,
    defaults={
        'name': tenant_name,
        'schema_name': schema_name,
    }
)
print(f"\n[1] Tenant: {t.slug} (created={created})")

# Step 2: Check existing TenantApp
ta = TenantApp.objects.filter(tenant=t, app_name='mattermost').first()
if ta:
    print(f"[2] Existing TenantApp: status={ta.status}, extra_config keys={list(ta.extra_config.keys()) if ta.extra_config else 'None'}")
    if ta.status == 'active':
        print("    Already active — will re-provision to validate.")
else:
    print("[2] No existing TenantApp — fresh provisioning.")

# Step 3: Provision Mattermost
print(f"\n[3] Provisioning Mattermost for {tenant_slug}...")
result = provision_mattermost_tenant(
    tenant_schema=t.schema_name,
    tenant_name=t.name,
    admin_email='polysaast27@example.com',
    company_name=t.name,
    admin_username='polysaast27',
    admin_password='PolySaaS2026!',
)

print(f"\n{'='*60}")
print("PROVISIONING RESULT:")
for k, v in sorted(result.items()):
    if k == 'success':
        print(f"  {k}: {v} {'PASS' if v else 'FAIL'}")
    else:
        print(f"  {k}: {v}")
print(f"{'='*60}")

if not result.get('success'):
    print("\nFAILED — provisioning did not succeed.")
    sys.exit(1)

# Step 4: Validate credentials work via Mattermost API
mm_url = result.get('mm_url', 'https://polysaas-mattermost.onrender.com')
username = result.get('mm_username', 'polysaast27')
password = 'PolySaaS2026!'

print(f"\n[4] Validating login via Mattermost API...")
print(f"    URL: {mm_url}")
print(f"    Username: {username}")

r = requests.post(
    f"{mm_url}/api/v4/users/login",
    json={"login_id": username, "password": password},
    timeout=10,
)

if r.status_code == 200:
    token = r.headers.get('Token')
    user = r.json()
    print(f"    Login: SUCCESS")
    print(f"    Token: {token[:15]}..." if token else "    Token: NONE")
    print(f"    User ID: {user.get('id')}")
    print(f"    Username: {user.get('username')}")

    # Step 5: Verify token works for /users/me
    if token:
        r2 = requests.get(
            f"{mm_url}/api/v4/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        print(f"    /users/me: {'PASS' if r2.status_code == 200 else 'FAIL'} (HTTP {r2.status_code})")

    # Step 6: Check team membership
    team_id = result.get('team_id')
    if team_id and token:
        r3 = requests.get(
            f"{mm_url}/api/v4/users/{user['id']}/teams",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r3.status_code == 200:
            teams = r3.json()
            team_names = [team['name'] for team in teams]
            print(f"    Teams: {team_names}")
            print(f"    Team membership: {'PASS' if team_id in [t['id'] for t in teams] else 'FAIL'}")
        else:
            print(f"    Teams check: FAIL (HTTP {r3.status_code})")

    print(f"\n{'='*60}")
    print("RESULT: PASS — t27 provisioned and credentials validated")
    print(f"{'='*60}")
else:
    print(f"    Login: FAIL (HTTP {r.status_code})")
    print(f"    Body: {r.text[:300]}")
    print(f"\n{'='*60}")
    print("RESULT: FAIL — credentials rejected by Mattermost")
    print(f"{'='*60}")
    sys.exit(1)
