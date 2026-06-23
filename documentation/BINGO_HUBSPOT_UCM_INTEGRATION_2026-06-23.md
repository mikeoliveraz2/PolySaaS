# BINGO — HubSpot Passthrough + User Context Manager

**Date:** 2026-06-23  
**Declared by:** Michael  
**Commit:** `28cc1155`  
**Tenancy model:** Each tenant connects **their own** HubSpot portal (OAuth per tenant)  
**API library:** Official `hubspot-api-client` (not immature `dj-hubspot` PyPI package)

---

## What Was Achieved

Two-track HubSpot integration:

| Track | Purpose | Entry |
|-------|---------|--------|
| **A — Passthrough** | Full HubSpot web UI in PolySaaS admin shell | Sidebar **HubSpot** → `/pt/admin/app.hubspot.com/…` |
| **B — User Context Manager (UCM)** | Native prioritized CRM portlets (not passthrough) | `/dose/hubspot/context/` |

---

## Certified behaviors (MVP)

| Feature | Status |
|---------|--------|
| `HubspotPassthroughHandler` auto-discovered via `matches_endpoint()` | ✓ |
| Per-tenant OAuth (`HUBSPOT_CLIENT_ID` / `SECRET` / redirect) | ✓ |
| Tokens stored on `TenantApp.extra_config` (`hs_access_token`, `hs_refresh_token`, `hs_portal_id`) | ✓ |
| Subscribe: **HubSpot CRM** checkbox + `provision_hubspot_tenant` | ✓ |
| UCM: Contacts, Companies, Deals, Tickets, Tasks portlets | ✓ |
| User drag-to-reorder portlet priority (persisted per user/tenant) | ✓ |
| Atomic services registered: `HubSpot*Portlet` | ✓ |
| Unit tests: `dose.tests.test_hubspot_integration` | ✓ |

---

## Architecture

```
Subscribe → provision_hubspot_tenant → PassThroughEndpoint + TenantApp (provisioning)
User → /dose/hubspot/oauth/start/ → HubSpot OAuth → tokens on TenantApp → active
UCM → /dose/api/hubspot/portlets/<slug>/ → HubspotApiService → hubspot-api-client
Passthrough → HubspotPassthroughHandler → app.hubspot.com (HTML rewrite + bypass rules)
```

---

## Files in This commit

| File | Role |
|------|------|
| `dose/passthrough/handlers/hubspot_handler.py` | Passthrough handler |
| `dose/services/hubspot_oauth.py` | OAuth authorize/callback/refresh |
| `dose/services/hubspot_api.py` | API wrapper + token refresh |
| `dose/services/hubspot_tenant_provisioner.py` | Subscribe provisioning |
| `dose/services/hubspot_portlet_services.py` | Portlet loaders + atomic services |
| `dose/models/hubspot_portlet.py` | `HubSpotPortletDefinition`, `UserHubSpotPortlet` |
| `dose/migrations/0052_hubspot_portlet_models.py` | Schema migration |
| `dose/views/hubspot_context.py` | UCM + OAuth views |
| `dose/templates/dose/hubspot_user_context.html` | UCM UI |
| `dose/templates/dose/hubspot_connect.html` | OAuth error/connect page |
| `dose/urls.py` | Routes |
| `dose/subscription_views.py` | `enable_hubspot` provisioner |
| `dose/models/tenant_app.py` | `hubspot` in `APP_CHOICES` |
| `dose/templates/dose/subscribe.html` | HubSpot checkbox + **PolySaaS Online** header |
| `dose/management/commands/seed_hubspot_portlets.py` | Seed portlets + optional Instructions |
| `dose/tests/test_hubspot_integration.py` | Unit tests |
| `mysite/settings.py` | `HUBSPOT_*` settings, subscribe enable list |
| `requirements.txt` | `hubspot-api-client==12.0.0` |
| `documentation/HUBSPOT_PASSTHROUGH_SNIFF_NOTES.md` | PolySniffer path/auth notes |

---

## Operator checklist

1. **Migrate all schemas:**
   ```powershell
   python manage.py migrate
   ```

2. **`.env` (or Secret Manager):**
   ```
   HUBSPOT_CLIENT_ID=...
   HUBSPOT_CLIENT_SECRET=...
   HUBSPOT_REDIRECT_URI=http://localhost:8000/dose/hubspot/oauth/callback/
   HUBSPOT_SCOPES=crm.objects.contacts.read crm.objects.companies.read crm.objects.deals.read tickets
   ```

3. **HubSpot developer app:** Add redirect URI matching `HUBSPOT_REDIRECT_URI`.

4. **Subscribe** with HubSpot enabled (or enable `TenantApp` manually).

5. **Connect OAuth:** `/dose/hubspot/oauth/start/` (or **Connect HubSpot** on UCM page).

6. **UCM:** `/dose/hubspot/context/` — reorder portlets, verify live CRM rows.

7. **Passthrough:** Sidebar **HubSpot** (requires HubSpot web session; OAuth alone powers API portlets).

8. **Optional seed:**
   ```powershell
   python manage.py seed_hubspot_portlets olient --instructions
   ```

---

## Tests

```powershell
python manage.py test dose.tests.test_hubspot_integration
```

---

## Known limits

- HubSpot SPA passthrough may require user web login inside proxied UI (OAuth tokens power API/UCM, not full SPA SSO).
- Run PolySniffer on production HubSpot session before hardening HTML rewrite rules further.
