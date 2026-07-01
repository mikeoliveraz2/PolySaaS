"""
End-to-end HubSpot Private App token test.

Verifies:
  1. Token is stored in TenantApp.extra_config for olient
  2. HubSpot API is reachable and returns contacts
  3. (Optional) syncs the first contact to Odoo via XML-RPC

Run:
    .\venv\Scripts\python.exe manage.py shell < tmp\_test_hs_api_token.py
  OR standalone (sets up Django env):
    .\venv\Scripts\python.exe tmp\_test_hs_api_token.py

Pass --sync to also test the Odoo write.
"""
import os
import sys
import django

# ── Bootstrap Django if running standalone ────────────────────────────────────
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
    django.setup()

from django.db import connection  # noqa: E402

TENANT_SLUG = "olient"
DO_ODOO_SYNC = "--sync" in sys.argv

# ── 1. Resolve token from TenantApp ──────────────────────────────────────────
print("=" * 60)
print(f"STEP 1: Load HubSpot token for tenant '{TENANT_SLUG}'")

with connection.cursor() as cur:
    cur.execute("SET search_path TO public")

from dose.models import Tenant, TenantApp  # noqa: E402

tenant = Tenant.objects.filter(slug=TENANT_SLUG).first()
if not tenant:
    print(f"FAIL: Tenant '{TENANT_SLUG}' not found.")
    sys.exit(1)

ta = TenantApp.public_bundles.filter(tenant=tenant, app_name="hubspot").first()
if not ta:
    print("FAIL: No HubSpot TenantApp found for olient.")
    print("  Run: python manage.py store_hubspot_token olient pat-na1-<your-token>")
    sys.exit(1)

extra = ta.extra_config if isinstance(ta.extra_config, dict) else {}
token = extra.get("hs_access_token") or ""
if not token:
    print("FAIL: hs_access_token is empty in TenantApp.extra_config.")
    print("  Run: python manage.py store_hubspot_token olient pat-na1-<your-token>")
    sys.exit(1)

masked = token[:12] + "..." + token[-4:] if len(token) > 16 else token
print(f"  Token (masked)  : {masked}")
print(f"  Portal ID       : {extra.get('hs_portal_id', '(unknown)')}")
print(f"  Token type      : {extra.get('hs_token_type', '?')}")
print()

# ── 2. Call HubSpot API — list contacts ──────────────────────────────────────
print("=" * 60)
print("STEP 2: HubSpot API — list 5 contacts")

try:
    from dose.services.hubspot_api import HubspotApiService  # noqa: E402

    svc = HubspotApiService(tenant, ta)
    contacts = svc.list_contacts(limit=5)
    if contacts:
        print(f"  SUCCESS — {len(contacts)} contact(s) returned:")
        for c in contacts:
            print(f"    id={c.get('id')}  name={c.get('firstname','')} {c.get('lastname','')}  email={c.get('email','')}")
    else:
        print("  API returned empty list (portal may have no contacts yet).")
except Exception as exc:
    print(f"  FAIL: {exc}")
    sys.exit(1)

print()

# ── 3. (Optional) Odoo sync test ─────────────────────────────────────────────
if DO_ODOO_SYNC:
    print("=" * 60)
    print("STEP 3: Odoo sync — push first HubSpot contact to Odoo")

    if not contacts:
        print("  SKIP: no contacts to sync.")
    else:
        first = contacts[0]
        # Build a minimal request-like object the sync service expects
        class _FakeRequest:
            tenant = None
            body = b""
            user = None

        fake_req = _FakeRequest()
        fake_req.tenant = tenant

        from dose.services.hubspot_to_odoo_contact_sync import HubSpotToOdooContactSync  # noqa: E402

        # Build the payload in HubSpot v3 shape
        import json
        props = {
            "email": first.get("email", ""),
            "firstname": first.get("firstname", ""),
            "lastname": first.get("lastname", ""),
            "phone": first.get("phone", ""),
            "company": first.get("company", ""),
        }
        fake_req.body = json.dumps({"properties": props}).encode()

        try:
            result = HubSpotToOdooContactSync._sync_to_odoo(
                HubSpotToOdooContactSync._get_odoo_config(fake_req),
                HubSpotToOdooContactSync._map_to_odoo_partner(props),
            )
            print(f"  Odoo result: {result}")
            if result.get("status") in ("created", "updated"):
                print(f"  SUCCESS — Odoo partner id={result.get('partner_id')}")
            else:
                print(f"  WARNING — unexpected status: {result.get('status')}")
        except Exception as exc:
            print(f"  FAIL: {exc}")

print()
print("=" * 60)
print("Done.")
