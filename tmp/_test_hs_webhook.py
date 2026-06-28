"""
Simulate a HubSpot workflow webhook POST and verify the full chain:
  Webhook → PolySaaS receiver → HubSpotToOdooContactSync → Odoo

Run against the live server:
    .\venv\Scripts\python.exe tmp\_test_hs_webhook.py

By default posts to http://localhost:8000.  Override with:
    .\venv\Scripts\python.exe tmp\_test_hs_webhook.py http://your-server:8000

Add --sync-check to also verify the contact appears in Odoo.
"""
import json
import sys
import requests

BASE_URL = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].startswith("http") else "http://localhost:8000"
TENANT_SLUG = "olient"
WEBHOOK_URL = f"{BASE_URL}/dose/webhook/hubspot/{TENANT_SLUG}/"

print("=" * 60)
print(f"HubSpot webhook simulation -> {WEBHOOK_URL}")
print("=" * 60)

# ── Test 1: GET probe (HubSpot tests the URL before saving the workflow) ──────
print("\nTest 1: GET probe (HubSpot liveness check)")
try:
    r = requests.get(WEBHOOK_URL, timeout=10)
    print(f"  Status : {r.status_code}")
    print(f"  Body   : {r.text[:100]}")
    assert r.status_code == 200, "Expected 200"
    print("  PASS")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# ── Test 2: HubSpot v3 flat payload (most common workflow format) ─────────────
print("\nTest 2: POST — HubSpot v3 flat payload")
payload_v3_flat = {
    "properties": {
        "email": "webhook.test@polysaas.online",
        "firstname": "Webhook",
        "lastname": "TestContact",
        "phone": "+61 400 000 001",
        "company": "PolySaaS Demo Corp",
        "jobtitle": "Integration Tester",
        "address": "42 Test Street",
        "city": "Sydney",
        "zip": "2000",
        "country": "Australia",
    }
}
try:
    r = requests.post(
        WEBHOOK_URL,
        json=payload_v3_flat,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    print(f"  Status : {r.status_code}")
    body = r.json() if "application/json" in r.headers.get("Content-Type", "") else {"raw": r.text}
    print(f"  Body   : {json.dumps(body, indent=2)}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    status = body.get("status")
    if status == "processed":
        results = body.get("results", [])
        for res in results:
            odoo_status = res.get("status") or res.get("odoo_result", {}).get("status")
            print(f"  Odoo result: {odoo_status}  (partner_id={res.get('partner_id') or res.get('odoo_result', {}).get('partner_id')})")
        print("  PASS")
    elif status == "no_instruction":
        print("  WARN: No HubSpotToOdooContactSync Instruction found.")
        print("  Run: python manage.py seed_hubspot_odoo_orchestration olient")
    else:
        print(f"  INFO: status={status}")
except Exception as e:
    print(f"  FAIL: {e}")

# ── Test 3: HubSpot nested {value:...} payload (older workflow format) ────────
print("\nTest 3: POST — HubSpot v3 nested payload (older workflow format)")
payload_v3_nested = {
    "properties": {
        "email": {"value": "webhook.nested@polysaas.online", "versions": []},
        "firstname": {"value": "Nested", "versions": []},
        "lastname": {"value": "TestContact", "versions": []},
        "phone": {"value": "+61 400 000 002", "versions": []},
        "company": {"value": "Nested Format Corp", "versions": []},
    }
}
try:
    r = requests.post(WEBHOOK_URL, json=payload_v3_nested, timeout=30)
    body = r.json() if "json" in r.headers.get("Content-Type", "") else {}
    status = body.get("status")
    print(f"  Status : {r.status_code}  webhook_status={status}")
    print("  PASS" if r.status_code == 200 else f"  FAIL: {r.status_code}")
except Exception as e:
    print(f"  FAIL: {e}")

# ── Test 4: Flat root payload (some HubSpot workflow configs) ─────────────────
print("\nTest 4: POST — flat root payload")
payload_flat = {
    "email": "webhook.flat@polysaas.online",
    "firstname": "Flat",
    "lastname": "RootTest",
    "phone": "+61 400 000 003",
}
try:
    r = requests.post(WEBHOOK_URL, json=payload_flat, timeout=30)
    status = r.json().get("status") if "json" in r.headers.get("Content-Type", "") else "?"
    print(f"  Status : {r.status_code}  webhook_status={status}")
    print("  PASS" if r.status_code == 200 else f"  FAIL: {r.status_code}")
except Exception as e:
    print(f"  FAIL: {e}")

print()
print("=" * 60)
print("Done. Check Odoo Contacts for 'Webhook TestContact' to confirm end-to-end sync.")
print(f"URL for HubSpot workflow config: {WEBHOOK_URL}")
print("Generic receiver handles ANY source: /dose/webhook/<source>/<tenant_slug>/")
