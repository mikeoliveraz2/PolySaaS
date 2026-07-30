# Security Fix — TenantApp Public Schema Leak (public_bundles removal)
**Date:** 2026-07-30
**Verified by:** AI agent session, local Docker stack (`dosedbsaas`)
**Status:** Fixed, migrated, verified ✓

---

## Background

This is the third time this exact class of bug surfaced (see
`HUBSPOT_ODOO_ORCHESTRATION_READY_2026-07-03.md` §1–2 for a prior one-off patch).
The root cause was never removed until now: a Django manager,
`TenantApp.public_bundles` (`dose/models/tenant_app.py`), forced the DB
connection's `search_path` to `public` on every access and left it there. Per
`.cursor/rules/tenant-isolation.mdc`, `TenantApp` is tenant-owned data (it
holds Odoo/Mattermost/Nextcloud/Dolibarr credentials, tokens, and session IDs
per tenant) and must live **only** in that tenant's own schema. `public_bundles`
made every tenant's app credentials readable/writable from the `public` schema
— a cross-tenant data leak — and also silently polluted `search_path` for
whatever code ran next in the same request/connection.

Per owner directive (Michael, 2026-07-30): *"Public should NEVER have tenant
specific data in it, NEVER, NEVER... Tenant schemas have tenant data, public
does not."* Full removal was explicitly approved, including in BINGO-frozen
files.

## What Was Done

### 1. Removed `PublicTenantAppBundleManager` entirely

`dose/models/tenant_app.py` — deleted the manager and the `public_bundles`
attribute. `TenantApp.objects` (default manager) is now the only way to query
this model; callers are responsible for setting `search_path` to the correct
tenant schema first (see `dose/tenant_app_lookup.py`).

### 2. Fixed all 15 call sites across 11 files

Every call site now uses `dose.tenant_app_lookup.tenant_schema_search_path()`
(or the by-name variant) to scope the query to the tenant's own schema:

- `dose/admin.py` — `PassThroughEndpointAdmin` subscription filter
- `dose/views/main.py` — dose home passthrough tile filter
- `dose/services/odoo_orchestration_provisioner.py`
- `dose/tenant_app_bundle.py` — `tenant_has_active_bundle()` (also fixed an
  unrelated pre-existing bug: `tenant.id` doesn't exist since `Tenant`'s PK
  field is `slug`; changed to `tenant.pk`)
- `dose/services/odoo_invoice_notifier.py`
- `dose/management/commands/cleanup_subscribe_test_artifacts.py`
- `dose/tests/test_tenant_membership.py`
- `dose/services/mattermost_tenant_provisioner.py` — 3 `public_bundles` sites
  plus 2 raw-SQL `SET search_path TO public` writes; the bulk
  `sync_mattermost_users_shared_team_landing()` cross-tenant query was
  rewritten to scan tenant schemas one at a time (TenantApp can no longer be
  queried in a single cross-schema statement)

**BINGO-frozen files (owner-approved exception, annotated inline rather than
re-certified):**

- `dose/passthrough/handlers/odoo_handler.py` — 3 `public_bundles` reads +
  `_clear_odoo_session_cache()` / `get_upstream_cookies()` saves
- `dose/passthrough/handlers/mattermost_handler.py` — 3 `public_bundles` reads
  (including removing two public-schema fallback branches in
  `_get_tenantapp_extra_config()` that could return a *different tenant's*
  credentials) plus 2 raw-SQL `SET search_path TO public` writes in
  `_save_tenantapp_token()` / `_save_tenantapp_config()`
- `dose/management/commands/provision_odoo_invoicing_orchestration.py` —
  `--all-odoo-active` now scans tenant schemas individually instead of one
  cross-tenant `public_bundles` query

### 3. Migrated the 14 rows already leaked into `public`

One-off script moved all 14 `public.dose_tenantapp` rows — and their linked
`public.oauth2_provider_application` rows (same root cause: OAuth Application
records were also created under `search_path=public`) — into their owning
tenant's own schema, then deleted the leaked copies from `public`.

`oauth2_provider_application.user_id` was dropped (set `NULL`) during the
move: that FK was bound to each tenant schema's own (separately-migrated,
initially empty) `auth_user` table copy, not `public.auth_user`, so the
original user reference couldn't resolve there. The field is unused by the
passthrough auth flow (client_id/client_secret matter, not user_id), and no
`AccessToken`/`Grant`/`RefreshToken` rows referenced any of the 14 leaked
Application ids, so nothing else needed migrating.

**Result:** `public.dose_tenantapp` and `public.oauth2_provider_application`
are now both empty (0 rows). `polysaas`, `psol6`, `pso7`, `pso8` each have
their own correctly-scoped `TenantApp` + `OAuth Application` rows.

### 4. Fixed `trigger_path` → `slug` stale-field bug (5 files)

`PassThroughEndpoint.trigger_path` was removed from the model in migration
`0048_remove_passthroughendpoint_trigger_path`, replaced by `slug`, but five
`update_or_create()` call sites (plus their debug print statements) were never
updated and would crash on first use:

- `dose/services/dolibarr_tenant_provisioner.py` (originally reported)
- `dose/services/liferay_tenant_provisioner.py`
- `dose/services/wordpress_tenant_provisioner.py`
- `dose/management/commands/setup_demo_sync.py`
- `dose/management/commands/setup_default_passthrough_endpoints.py`

## Verification

- `python manage.py check` — 0 issues
- Restarted Waitress (`mysite.wsgi:application`) to load all changes
- `GET /dose/home/` and `GET /admin/` as a tenant admin (schema `pso7`) — both
  200, no `AttributeError`/`public_bundles` references
- `tenant_has_active_bundle()` correctly resolves per-tenant status from the
  tenant's own schema
- `OdooPassthroughHandler._get_tenantapp_extra_config()` and
  `MattermostPassthroughHandler._get_tenantapp_extra_config()` /
  `_expected_mm_username()` tested directly against real tenant-schema data
  (`polysaas` tenant's real Mattermost credentials resolved correctly)
- **Cross-tenant isolation proof:** with the DB connection's ambient
  `search_path` deliberately left on tenant `pso7`, calling the Odoo handler
  with `request.tenant` = `polysaas` still returned `polysaas`'s own data
  (identical to calling it with ambient search_path reset first) — the fix
  no longer depends on, or leaks via, whatever schema the connection happens
  to be pointed at
- `search_path` confirmed restored to its prior value after each
  `tenant_schema_search_path()` context exits (no pollution)

## Known Follow-up (not fixed — flagged for owner decision)

The `trigger_path` field removal left a **much wider** latent bug: dozens of
places across `dose/signals.py`, `dose/polysniffer/*` (views, ai_analysis,
structured_capture, sniff_forward, handlers/base.py), `dose/serializers.py`,
`dose/passthrough/registry.py`, `dose/passthrough/handlers/dolibarr_handler.py`,
and a couple of management commands still do **direct** `.trigger_path`
attribute access or `.filter(trigger_path=...)` queries against a column that
no longer exists on the model. `getattr(obj, "trigger_path", None)` call sites
are safe (return `None`); direct attribute/filter access will raise
`AttributeError`/`FieldError` the first time that code path executes. This is
a separate, larger cleanup — intentionally out of scope for this fix.

## Files Changed

See commit for full diff. `.bak_20260730_pubbundles` backups were made for
every file before editing, per `bak-before-edit.mdc`.
