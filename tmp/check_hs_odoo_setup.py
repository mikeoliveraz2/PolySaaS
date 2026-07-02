"""
Check HubSpot->Odoo orchestration setup and test Odoo connectivity for olient.
"""
import sys
from django.db import connection

SCHEMA = 'olient'

# Instructions live in the tenant schema
with connection.cursor() as cur:
    cur.execute(f'SET search_path TO {SCHEMA},public;')

from dose.models import Instruction, Tenant

tenant = Tenant.objects.get(slug=SCHEMA)
print(f"Tenant: {tenant.name} (schema={tenant.schema_name})")

# --- Instructions in olient ---
print("\n=== Instructions (olient) ===")
for inst in Instruction.objects.filter(tenant=tenant):
    print(f"  pk={inst.pk} eventKey={inst.eventKey} executescript={inst.executescript} match={inst.requestpath}")

# TenantApp lives in public schema
with connection.cursor() as cur:
    cur.execute('SET search_path TO public;')

from dose.models import TenantApp

print("\n=== Odoo TenantApp (from public) ===")
ta = TenantApp.objects.filter(tenant=tenant, app_name='odoo').first()
if ta:
    cfg = ta.extra_config or {}
    print(f"  status       = {ta.status}")
    print(f"  odoo_url     = {cfg.get('odoo_url')}")
    print(f"  odoo_login   = {cfg.get('odoo_login')}")
    print(f"  odoo_db      = {cfg.get('odoo_db')}")
    print(f"  odoo_user_id = {cfg.get('odoo_user_id')}")
    print(f"  odoo_session = {cfg.get('odoo_session_id')}")
else:
    print("  NOT FOUND in public schema either")

# --- Test Odoo connectivity ---
print("\n=== Odoo Connectivity Test ===")
if ta:
    import requests
    cfg = ta.extra_config or {}
    odoo_url = cfg.get('odoo_url', '').rstrip('/')
    odoo_db  = cfg.get('odoo_db')
    login    = cfg.get('odoo_login')
    password = cfg.get('odoo_password')

    print(f"  Target: {odoo_url}")
    try:
        # Version check (no auth)
        resp = requests.get(f"{odoo_url}/web/webclient/version_info", timeout=20)
        print(f"  Version endpoint: HTTP {resp.status_code}")

        # Authenticate
        auth_payload = {
            "jsonrpc": "2.0", "method": "call",
            "params": {"db": odoo_db, "login": login, "password": password}
        }
        auth_resp = requests.post(
            f"{odoo_url}/web/session/authenticate",
            json=auth_payload, timeout=30
        )
        auth_data = auth_resp.json()
        result = auth_data.get('result', {})
        uid    = result.get('uid')
        error  = auth_data.get('error')
        if uid:
            session_id = auth_resp.cookies.get('session_id')
            print(f"  AUTH SUCCESS: uid={uid}, name={result.get('name')}")
            print(f"  session_id={session_id}")

            # Save session_id back to TenantApp
            cfg['odoo_session_id'] = session_id
            ta.extra_config = cfg
            ta.save()
            print(f"  Saved session_id to TenantApp pk={ta.pk}")
        else:
            print(f"  AUTH FAILED: {error or result}")
    except Exception as e:
        print(f"  ERROR: {e}")
else:
    print("  Skipping - no TenantApp found")

print("\nDone.")
