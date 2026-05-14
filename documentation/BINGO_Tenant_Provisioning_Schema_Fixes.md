# BINGO — Tenant Provisioning + Schema Migration Fixes

**Date**: 2026-05-15
**Status**: ✅ COMPLETE
**Branch**: `main`

---

## Result
- Tenant schema migrations run synchronously after DB commit, before provisioners execute
- New tenant schemas have all required tables before provisioners insert `PassThroughEndpoint` records
- Passthrough apps (Odoo, NextCloud) appear immediately in tenant admin sidebar after subscription
- Secret Manager no longer hangs server on startup; fails fast and falls back to `.env`
- `trigger_path` → `slug` field migration applied cleanly; all provisioners and passthrough registry updated

---

## Root Causes Fixed

### 1. Tenant schema empty at provision time
- `Tenant.save()` created empty schema inside atomic transaction
- Provisioners ran after commit but found no tables (`relation "dose_passthroughendpoint" does not exist`)
- **Fix**: `_register_provisioning_synchronous` now calls Django's original `MigrateCommand` directly on the tenant schema after commit and before any provisioner runs

### 2. Secret Manager startup hang
- `access_secret_version` with default gRPC retry hung for minutes on localhost without ADC
- **Fix**: Added `timeout=3.0` and `retry=None` to fail fast; marks client unavailable on auth errors so `.env` fallback is used immediately

### 3. `trigger_path` field removal incomplete
- Model dropped `trigger_path` in favor of `slug`, but DB still had the column (NOT NULL constraint)
- Odoo/Nextcloud provisioners tried to write to removed field → `Cannot resolve keyword 'trigger_path'`
- Passthrough registry and path rewrite middleware still referenced `endpoint.trigger_path`
- **Fix**: Created migration `0048_remove_passthroughendpoint_trigger_path.py`; updated all provisioners and passthrough code to use `slug`

### 4. Mattermost provisioning sidebar gap
- Early-exit on team creation failure meant `PassThroughEndpoint` was never created
- **Fix**: Moved `_ensure_passthrough_endpoint` before the early-exit so sidebar entry always exists regardless of MM API success

### 5. Custom migrate command recursion
- `call_command('migrate')` triggered the custom multi-schema migrate command which looped over all tenants
- **Fix**: Invoke Django's original `MigrateCommand` class directly instead of `call_command`

---

## Files Changed

| File | Change |
|------|--------|
| `dose/subscription_views.py` | Run original Django migrate on tenant schema after commit; removed `call_command` import; all provisioning synchronous with debug prints |
| `dose/utils/secret_manager.py` | `timeout=3.0`, `retry=None`, mark unavailable on auth failure |
| `dose/services/odoo_tenant_provisioner.py` | Use `slug='odoo'` instead of `trigger_path='odoo'` |
| `dose/services/nextcloud_tenant_provisioner.py` | Use `slug='nextcloud'` instead of `trigger_path='nextcloud'` |
| `dose/services/mattermost_tenant_provisioner.py` | Move `_ensure_passthrough_endpoint` before early-exit on team failure |
| `dose/passthrough/handlers/registry.py` | Use `endpoint.slug` instead of `endpoint.trigger_path` |
| `dose/passthrough/incoming_path_rewrite.py` | Use `endpoint.slug` instead of `endpoint.trigger_path` |
| `mysite/settings.py` | Updated secret name format to uppercase `MATTERMOST_ADMIN_TOKEN` |
| `dose/migrations/0048_remove_passthroughendpoint_trigger_path.py` | Removes deprecated `trigger_path` column |

---

## Follow-ups

| Priority | Task |
|----------|------|
| 1 | **Fix Mattermost provisioner silent failure** — endpoint not created at all; provisioner appears to hang/crash before `_ensure_passthrough_endpoint` runs |
| 2 | Fix Odoo passthrough client asset loading error (`owl lifecycle`) |
| 3 | Fix Nextcloud provisioner 404 — verify instance URL |
| 4 | Update `MATTERMOST_ADMIN_TOKEN` in `.env` (expired, causes 401) |
