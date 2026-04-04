# BINGO: Passthrough Filter & Admin Cleanup

**Date:** 2026-04-04  
**Status:** ✅ Tested and confirmed by user — "bingo"

## What Was Done

### 1. Passthrough Sidebar Filter (context_processors.py + views/main.py)
- Sidebar now shows **only subscribed bundled apps + gmail** (always)
- Removed the "custom/unknown always show" fallback that was leaking unsubscribed entries
- Trigger path normalisation: `strip('/').lower().split('/')[-1].replace('-','_')`
  - `/Admin/Passthrough/Odoo/` → `odoo`
  - `monitor-logger` → `monitor_logger`
- Deduplication uses the same normalised key — path-based and simple-name duplicates collapse to one
- URL always built from normalised name: `/pt/admin/{norm}/`

### 2. PassThroughEndpoint Admin List Filter (admin.py)
- `get_queryset` filters to subscribed apps only using `qs.only('id','trigger_path')` 
  — safe evaluation that can never hit missing-column errors
- Tenants only see and edit endpoints they are subscribed to

### 3. Admin Transaction Fix (admin.py)
- AUTO-FIX DDL wrapped in `transaction.atomic()` savepoint — failure can no longer poison the outer request transaction
- Switched to `ADD COLUMN IF NOT EXISTS` — idempotent, never raises an error
- Removed phantom fields `polysniffer_last_run` / `polysniffer_debug_output` from columns_to_add and defer() — these were added by a previous AI without authorisation and are not model fields

### 4. Djstripe Hidden from Admin (settings.py)
- Added `"hide_apps": ["djstripe"]` to JAZZMIN_SETTINGS
- Stripe internals no longer clutter the tenant admin interface

### 5. ML Prompts Hidden from Dose Section (settings.py)
- Added `"dose.mlprompt"` to `hide_models`
- ML Prompts now only visible under Machine Learning Studio

### 6. Data Fixes
- `liferay` PassThroughEndpoint created in all schemas (was missing)
- `wordpress` TenantApp added to `mggp` tenant
- All path-based trigger_paths cleaned across all 5 schemas:
  - `/dose/monitor/` → `monitor_logger`
  - `/dose/osticket/` → `osticket`
- `WordPress` trigger capitalisation fixed → `wordpress`

### 7. Design Principle Locked In
Every tenant schema is provisioned with the **full complement of endpoints**.  
Sidebar and admin list filter by TenantApp subscription at display time only.  
Upgrading a tenant = add a TenantApp row. No new endpoint records needed.

### 8. Profile Page Polish (templates/account/profile.html)
- Title/heading: "Welcome to DOSE!" → "Welcome to PolySaaS!" + logo
- Removed "Test Jira Access" button
- "Django Admin" → "Admin Dashboard"
- API link: `/api/` → `/swagger/`

## Files Changed
- `dose/context_processors.py` + `.bak`
- `dose/views/main.py` + `.bak`
- `dose/admin.py` + `.bak`
- `mysite/settings.py` + `.bak`
- `templates/account/profile.html` + `.bak`
- `docs/bingo/profile-page-polish.md`
