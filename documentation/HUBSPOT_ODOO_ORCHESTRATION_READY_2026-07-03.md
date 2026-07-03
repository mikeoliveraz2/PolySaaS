# HubSpot → Odoo Dynamic Orchestration — READY
**Date:** 2026-07-03  
**Verified by:** Michael Oliver  
**Status:** End-to-end working ✓

---

## What Was Done

### 1. Schema Fix — olient.dose_tenantapp missing column

**Root cause:** Migration `0023_tenantapp_oauth_application_optional` uses an
`information_schema.columns` check with no `table_schema` filter.  When
`public.dose_tenantapp` already had `oauth_application_id`, the check returned
true and skipped the `ALTER TABLE` for the `olient` schema.  All 56 `dose`
migrations were recorded in `olient.django_migrations` but the column was never
added to `olient.dose_tenantapp`.

**Fix applied (2026-07-03):**
```sql
ALTER TABLE olient.dose_tenantapp
ADD COLUMN IF NOT EXISTS oauth_application_id integer NULL;
```

Script: `tmp/fix_olient_tenantapp_column.py`

---

### 2. TenantApp Placement Fix — moved Odoo record to olient schema

**Root cause:** The Odoo `TenantApp` row (provisioned earlier) was in
`public.dose_tenantapp`.  Per tenant isolation rules, `TenantApp` is a
tenant-scoped model that must live in the tenant schema.  When the webhook
receiver sets `search_path TO olient, public`, the ORM finds `olient.dose_tenantapp`
(empty) before `public.dose_tenantapp`, and falls back to the `localhost:8069`
defaults.

**Fix applied (2026-07-03):**  
Copied Odoo TenantApp row from `public` to `olient`:

| Field | Value |
|---|---|
| `app_name` | `odoo` |
| `odoo_url` | `https://polysaas-odoo2.onrender.com` |
| `odoo_login` | `michael.oliver@polysaas.online` |
| `odoo_db` | `polysaas_odoo` |
| `odoo_user_id` | `31` |
| `status` | `active` |

Script: `tmp/move_odoo_tenantapp_to_olient.py`

---

### 4. TenantApp Placement Fix — moved HubSpot record to olient schema

**Root cause:** HubSpot `TenantApp` (Playwright cookies, `hs_hub_subdomain`, OAuth
tokens) lived in `public.dose_tenantapp` while passthrough and session code must
read tenant-owned rows from the tenant schema (`olient`).

**Fix applied (2026-07-03):**
- Shared helper: `dose/tenant_app_lookup.py` — all tenant-schema TenantApp reads/writes
- `get_tenant_hubspot_app()` → tenant schema (not `public_bundles`)
- `provision_hubspot_session`, `store_hubspot_token` → write to `{schema}.dose_tenantapp`
- Data copy: `tmp/move_hubspot_tenantapp_to_olient.py`

---

### 3. End-to-End Test — PASSED

Webhook fired at:
```
POST http://localhost:8000/dose/webhook/hubspot/olient/
```

Payload (HubSpot v3 flat format):
```json
{
  "properties": {
    "firstname": "July", "lastname": "TestContact",
    "email": "july.testcontact.2026@polysaas-test.com",
    "phone": "+61 2 5550 1234", "company": "PolySaaS Test Co",
    "jobtitle": "Test Manager", "city": "Sydney", "country": "Australia",
    "website": "https://polysaas-test.com"
  }
}
```

Result:
- Instruction 3 (`hubspot:contact:created:v3`) → **CREATED** `res.partner id=34` in Odoo
- Instruction 4 (`hubspot:contact:created:v1`) → **UPDATED** same partner (idempotent dedup by email)
- Odoo instance: `https://polysaas-odoo2.onrender.com`
- Country resolved: `Australia` → `country_id`
- Company resolved/created: `PolySaaS Test Co`

Test script: `tmp/test_hs_odoo_webhook.py`

---

## Architecture Summary

```
HubSpot (workflow trigger)
        │
        ▼
POST /dose/webhook/hubspot/olient/
        │
        ▼
generic_inbound_webhook (dose/views/generic_inbound_webhook.py)
  ├─ Resolves tenant: olient (Oliver Enterprises)
  ├─ Sets search_path TO olient, public
  ├─ Finds Instructions: hubspot:contact:created:v3 + v1
  └─ Dispatches: HubSpotToOdooContactSync.execute_and_save()
        │
        ▼
HubSpotToOdooContactSync (dose/services/hubspot_to_odoo_contact_sync.py)
  ├─ Parses HubSpot payload (Shapes 1-5 supported)
  ├─ Maps via Mapping engine (hs-contact-to-odoo-partner)
  ├─ Reads Odoo config from olient.dose_tenantapp
  └─ Syncs to Odoo via XML-RPC (create or update res.partner)
        │
        ▼
Odoo: https://polysaas-odoo2.onrender.com
  └─ res.partner created/updated (dedup by email)
```

---

## Production Webhook URL

For real HubSpot → Odoo sync, configure a HubSpot workflow:
- **Trigger:** Contact created / property updated
- **Action:** Send HTTP request
- **URL:** `https://polysaas.online/dose/webhook/hubspot/olient/`
- **Method:** POST
- **Body:** HubSpot default contact properties (v3 flat format works)

---

## Seeded Instructions (olient schema)

| pk | eventKey | executescript | match |
|----|---|---|---|
| 3 | `hubspot:contact:created:v3` | `HubSpotToOdooContactSync` | `/crm/v3/objects/contacts` |
| 4 | `hubspot:contact:created:v1` | `HubSpotToOdooContactSync` | `/contacts/v1/contact` |

Mapping: `hs-contact-to-odoo-partner` (10 fields)

---

## Known Limitations / Next Steps

1. **HubSpot workflow not yet configured** — the webhook URL above needs to be entered in a real HubSpot workflow to trigger on live contact creation.
2. **Odoo on Render cold starts** — if Render spins down the free tier, first sync after idle may time out. Odoo re-authenticates on each XML-RPC call.
3. **No retry on failure** — if Odoo is unreachable, the webhook returns 200 (so HubSpot does not retry) but the sync is lost. A retry queue via CallBackData could be added later.
