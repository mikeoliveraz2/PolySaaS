# BINGO — Odoo Provisioning + Passthrough (May 2026)

**Date:** 2026-05-31  
**Status:** Provisioning flow fixed; passthrough false-positive error page fixed  
**Verified tenant:** `polysaast121` (PolySaaS Test 121)

---

## What Was Broken

1. **Subscribe showed “Odoo is ready” but sidebar failed** — OAuth registration could fail while the Celery/XML-RPC provisioner still created the Odoo user and PassThroughEndpoint. No `TenantApp` row meant no credentials in `extra_config`, so passthrough fell back to the shared admin login.

2. **Wrong XML-RPC admin** — `ODOO_SHARED_ADMIN_LOGIN` (`pst13@me.com`) lacks Access Rights to create users. Provisioning silently failed until `ODOO_XMLRPC_ADMIN_LOGIN` (`odooAdmin`) was split out.

3. **Credential mismatches** — Signup password was not passed to the provisioner; `odoo_db` was stored as tenant schema name instead of `odoodb`.

4. **“Odoo Access Not Ready” false positive** — `_is_database_selector_page()` matched the normal `/web/login` page (`name="login"` + “Powered by Odoo”). Iframe requests with `?__pss_raw=1` did not strip the query string from path checks, so login HTML triggered the error page even when the user existed.

5. **`process_html_response` regression** — Handler method body was accidentally nested inside `_is_web_login_html()` (dead code); restored as a proper method.

---

## Fixes

### Provisioning (`dose/services/odoo_tenant_provisioner.py`)

- Reports real success/failure (no demo mode).
- Accepts `admin_password` from signup.
- Uses `ODOO_XMLRPC_ADMIN_LOGIN` for XML-RPC (defaults to `odooAdmin`).
- Fixed `mark_tenant_app_error()` call and `TenantApp` import scoping bug.

### Subscribe (`dose/subscription_views.py`)

- `TenantApp.objects.get_or_create()` **before** OAuth — OAuth failure no longer skips the row.
- Odoo credentials stored in `extra_config` before provisioning runs.
- Success message only when `TenantApp.status == 'active'`.
- Session credential container stores `odoo_db`.

### Settings (`mysite/settings.py`)

- `ODOO_XMLRPC_ADMIN_LOGIN` — provisioning admin (Access Rights).
- `ODOO_SHARED_ADMIN_LOGIN` — passthrough fallback display login unchanged.

### Passthrough (`dose/passthrough/handlers/odoo_handler.py`)

- Restored `process_html_response()`.
- `_upstream_subpath()` strips query string (`/web?__pss_raw=1` → `/web`).
- Strict database-selector detection (no `name="login"` heuristic).
- Skip error page on login/shell paths and login HTML — auto-login shim handles those.
- `get_upstream_credentials()` reads session container, TenantApp, and user email.

### Management / diagnostics

- `python manage.py repair_tenant_odoo <slug>` — re-provision or repair stuck tenants.
- `python manage.py check_tenant_odoo <slug>` — inspect TenantApp + credentials.
- `python check_odoo_user.py <email>` — verify user exists in Odoo via XML-RPC.

---

## Verification (polysaast121)

```text
TenantApp status: active
odoo_login: pst121@you.com
odoo_db: odoodb
odoo_user_id: 75
Odoo XML-RPC: user 75 active
```

After fixes: sidebar Odoo link should load iframe shell → auto-login → Odoo apps grid (not “Access Not Ready”).

---

## Operational Notes

- **New signups:** Should get TenantApp + credentials even if OAuth fails.
- **Old tenants missing Odoo TenantApp:** Run `repair_tenant_odoo` once (optional; not run for legacy test tenants per Michael).
- **Welcome email:** Requires `gmail_creds.json` locally (non-fatal if missing).

**Status: BINGO — Odoo provisioning + passthrough path green for new subscribe flow.**
