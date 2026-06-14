# Session Handoff — polysaasppd Subscribe, Odoo Orchestration, Passthrough Sidebar

**Date:** 2026-06-15  
**Machine:** Laptop (`F:\PolySaaS`) → office sync via `git pull origin main`  
**Tenant focus:** `polysaasppd` (PolySaaS Pre Production Demo)

---

## Executive Summary

This session fixed **new-subscriber Odoo invoicing orchestration** and **tenant-scoped CallBackData**, then restored the **PASSTHROUGH SERVICES** sidebar for `polysaasppd` and future signups. Root causes were schema/type mismatches, search_path bugs, missing endpoint catalog rows, and a Jazzmin middleware crash on removed `trigger_path`.

---

## Commits on `main` (chronological)

| Commit | Summary |
|--------|---------|
| `1b80079d` | Migration 0051 (tenant_slug varchar); orchestration provisioner search_path fix; CallBackData tenant isolation |
| `d492e770` | Passthrough endpoint seed on subscribe; Jazzmin `trigger_path` → hostname fix |
| *(this push)* | Jazzmin `process_request` actually runs; `seed_passthrough_endpoints` management command; session doc |

---

## Problem 1 — Odoo invoicing orchestration failed on new tenants

### Symptom
`polysaasppd` Odoo passthrough: no instruction match, no CallBackData.

### Root causes
1. **`polysaasppd` schema had no tables** until `migrate_all_schemas` ran (subscribe inline migrate may have failed silently for this tenant).
2. **`dose_instruction.tenant_slug` stayed `bigint`** after migration 0036 slug-PK change; migrations 0041/0042 only fixed navigation/dashboard tables. Provisioning failed with:
   ```
   invalid input syntax for type bigint: "polysaasppd"
   ```
3. **Provisioner search_path bug:** `TenantApp.public_bundles` resets `search_path` to `public`, so Instructions were inserted into **`public`** while orchestration reads the **tenant schema** (empty table shadows public after migrate).

### Fixes
- **`dose/migrations/0051_alter_remaining_tenant_slug_columns_to_varchar.py`** — converts all remaining `dose_*` `tenant_slug`/`tenant_id` bigint columns to varchar on every schema at migrate time.
- **`odoo_orchestration_provisioner.py`** — re-set tenant `search_path` after TenantApp update (`.bak` alongside).
- **Backfill for `polysaasppd`:** 3 Instructions in tenant schema (ids 2–4): `/odoo/accounting/119`, `/odoo/accounting`, `account.move/web_search_read`.

### Subscribe flow (automatic for new Odoo subscribers)
```
Subscribe → migrate tenant schema (0051 applies) → seed PassThroughEndpoints
         → provision Odoo → provision_odoo_invoicing_orchestration(tenant)
```

---

## Problem 2 — CallBackData must be per-tenant only

### Fixes (`1b80079d`)
- **`atomic_service_utils.maybe_save_callback`** — requires tenant + `ensure_tenant_search_path` before create.
- **`data_extractor` / `odoo_customer_sync`** — same guard on direct creates.
- **`callbackdata_view` / `callback_log_viewer`** — login + active tenant schema only; no cross-tenant browse.
- **`TenantScopedViewSetMixin`** — sets tenant schema on DRF list/create/update/delete.

Orchestration hook (`orchestration_hook.py`) already used `ensure_tenant_search_path` for saves (unchanged, frozen).

---

## Problem 3 — Passthrough sidebar missing for `polysaasppd`

### Symptom
Admin sidebar showed HOME → CONTROLS → SYSTEM NAVIGATION; **no PASSTHROUGH SERVICES** panel (see screenshot in chat).

### Root causes
1. **Zero `PassThroughEndpoint` rows** in `polysaasppd` schema (subscribe migrated tables but never copied endpoint catalog).
2. **Jazzmin middleware** referenced removed **`trigger_path`** → exception → `request.passthrough_endpoints = []`.
3. **`DebugStackMiddleware.__call__`** bypassed `MiddlewareMixin.process_request`, so Jazzmin setup never ran until fixed.

### Fixes
- **`dose/management/passthrough_seed.py`** + call from **`subscription_views.py`** after migrate.
- **`d492e770`** — Jazzmin uses `endpoint_url` hostname; `TenantApp.public_bundles` for lookups.
- **Backfill:** 3 endpoints seeded in `polysaasppd` (Odoo, NextCloud, Mattermost).
- **`JazzminTenantThemeMiddleware.__call__`** — calls `process_request` before `super().__call__`.
- **`manage.py seed_passthrough_endpoints`** — manual backfill for existing tenants.

### Verify at office
1. `git pull origin main`
2. `python manage.py migrate_all_schemas --no-input`
3. Restart server (`.\runall.ps1` on F:, `D:\PolySaaS` on office)
4. Login as `polysaasppd` → `/admin/` → hard refresh (Ctrl+F5)
5. Browser console should show: `passthrough_services count: 3`
6. Sidebar should show **PASSTHROUGH SERVICES** with Odoo / NextCloud / Mattermost cards

Optional backfill:
```powershell
python manage.py seed_passthrough_endpoints polysaasppd
python manage.py provision_odoo_invoicing_orchestration polysaasppd
```

---

## Files Touched This Session

| Area | Files |
|------|-------|
| Migration | `dose/migrations/0051_alter_remaining_tenant_slug_columns_to_varchar.py` |
| Subscribe | `dose/subscription_views.py`, `dose/management/passthrough_seed.py` |
| Odoo orch | `dose/services/odoo_orchestration_provisioner.py` (+ `.bak`) |
| CallBackData | `dose/services/atomic_service_utils.py`, `data_extractor.py`, `odoo_customer_sync.py`, `dose/views/callbackdata.py`, `dose/tenant_enforcement.py` (+ `.bak` each) |
| Sidebar | `dose/middleware/jazzmin_tenant_theme.py` (+ `.bak`, `.bak2`) |
| Command | `dose/management/commands/seed_passthrough_endpoints.py` |

### Not committed (local only)
- `runall.ps1` encoding fix (em-dash → `--`)
- Diagnostic scripts under `scripts/_*.py`
- Mattermost WIP / HAR compare files

---

## Office Checklist

```powershell
cd D:\PolySaaS   # or F:\PolySaaS on laptop
git pull origin main
.\venv\Scripts\activate
python manage.py migrate_all_schemas --no-input
.\runall.ps1
```

Test Odoo invoicing on `polysaasppd`: expect green orchestration bar + CallBackData rows after invoice list load.

---

## Known Separate Track

**Mattermost passthrough SSO** — WIP on `wip` branch/worktree; not blocking Odoo demo. Rule: no team logic in passthrough (`mattermost-passthrough-no-team.mdc`).

---

## Addendum — `runall.ps1` encoding fix (2026-06-15)

### Symptom
`.\runall.ps1` failed on Windows with PowerShell parse errors (`Missing argument`, `Unexpected token 'PIDs'`) because Unicode em-dashes (`—`) were corrupted to `â€"` under UTF-8 without BOM.

### Fix
- Replace em-dashes with ASCII `--` in all `Write-Host` / `throw` strings.
- Use single-quoted strings where `@grok @gemini @copilot` would expand as splatting.
- Save as UTF-8 with BOM so Windows PowerShell reads the file reliably.

### Verify
```powershell
.\runall.ps1
```
Should complete with `PolySaaS runall -- complete` and no parser errors.

### Cursor workspace launcher
- `runwt.ps1` / `runwt.bat` — starts Waitress from workspace root with venv + PYTHONPATH (for F: laptop / Cursor).
