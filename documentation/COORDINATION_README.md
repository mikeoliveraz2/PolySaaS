# PolySaaS Coordination Log

This document tracks session activity across machines (laptop/desktop) for synchronization.

---

## 2026-05-04 — The "Stupid Debug Session" (Paradigm Shift)

**Status**: Debugging in progress  
**Branch**: main  
**Time**: ~6 hours of cloud-deploy-debug iterations before realizing local dev is the only sane approach

### Summary
Spent 6+ hours debugging Odoo passthrough blank screen issue using the **insane** methodology: edit code → commit → push → wait for Render deploy → check gimpy logs → repeat. This is the **wrong way** to debug. Both user and assistant failed to recognize this immediately.

The actual working approach: **Develop and test locally first**, then deploy once it's working. User has full local setup (Postgres, Docker apps) but wasn't using it for passthrough debugging.

### Key Issues Discovered

**1. Template Missing Bug**
- `_wrap_in_admin_template()` in `middleware.py` tried to render `admin/passthrough_embed.html` which **did not exist**
- Created `templates/admin/passthrough_embed.html` to fix

**2. Odoo Auto-Init Bug**
- Entrypoint script checked if `ir_module_module` **table existed**, not if `web` module was **installed**
- Database had empty tables from failed init → `web.login` template not found → 500 errors
- Fixed entrypoint to check `SELECT state FROM ir_module_module WHERE name = 'web'`

**3. Handler Returns None for /web/login**
- `try_root_display_shell_response` returns `None` for non-root paths
- Falls through to forwarder, which wraps raw Odoo response
- This is actually working as designed (handler only handles root path redirect)

**4. 502 Error Handling**
- Added better error display when upstream service returns 502/503/504 instead of blank page

### Root Cause of Blank Page
The blank page persists despite fixes. Current theory:
1. Handler returns `None` for `/web/login` → falls through to forwarder
2. Forwarder gets 200 OK from Odoo with valid HTML
3. `_is_initial_page_load()` may be returning `False` for some reason (treating HTML as API/asset)
4. OR the wrapped template is rendering empty content

**Next Step**: Test locally with full debug output to see exactly what `_is_initial_page_load` decides and what the wrapped HTML looks like.

### Files Changed Today
1. `templates/admin/passthrough_embed.html` — CREATED (missing template)
2. `deploy/odoo-render/entrypoint-render.sh` — FIXED (check web module state, not just table existence)
3. `dose/passthrough/middleware.py` — ADDED error handling for 502/503/504

### Paradigm Shift
**OLD (stupid) workflow:**
- Edit → Commit → Push → Wait 2-5 min for deploy → Check gimpy Render logs → Repeat
- 6+ hours, no resolution

**NEW (correct) workflow:**
- Run Core locally on localhost:8000
- Test passthrough pointing to Render Odoo (or local Docker Odoo)
- Full console logs, instant turnaround, can use debugger
- When working, commit → push → quick Render verification

### Next Session (2026-05-05)
**User will:**
1. Set `DOSE_DB_PASSWORD` in `.env` for local Postgres
2. Run `python manage.py runserver`
3. Access `http://localhost:8000/admin/`
4. Click Odoo passthrough link
5. Check full debug output in console

**Or:** Test via URL directly: `http://localhost:8000/pt/admin/polysaas-odoo2.onrender.com/web/login`

**Assistant will:**
- Help interpret local debug output
- Fix whatever `_is_initial_page_load` or wrapper issue is causing blank page
- Once working locally, commit and push to Render

---

## 2026-04-29
**Status**: In Progress
**Branch**: main

### Summary
Explored existing passthrough infrastructure and implemented permanent passthrough infrastructure for Odoo and Mattermost. This is production infrastructure, not a one-off demo - users subscribe and have instant access to the apps they subscribed to. Confirmed both Odoo and Mattermost passthrough handlers already exist and are PolySniffer-generated for dynamic event capture during passthrough sessions.

### Key Findings
- **PassthroughAuthMiddleware**: Injects auth headers/JWT on `/pt/` paths with tenant info (tenant_slug, tenant_name)
- **OdooPassthroughHandler**: Comprehensive handler with display shell, auto-login via JSON-RPC, path rewriting, WebSocket support
- **MattermostPassthroughHandler**: Comprehensive handler with display shell, auto-login via MMAUTHTOKEN, WebSocket/fetch/XHR patching
- **Handler Registry**: Both handlers registered with trigger_path matching
- **PassThroughEndpoint model**: Stores endpoint configuration (trigger_path, endpoint_url, menu integration)
- **TenantApp model**: Tracks which apps are provisioned per tenant (odoo, mattermost, nextcloud, etc.)
- **Subscription flow**: Automatically creates TenantApp records when users select apps during subscription
- **Tenant provisioners**: Both odoo_tenant_provisioner.py and mattermost_tenant_provisioner.py exist and are wired to subscription

### Files Reviewed
- `dose/middleware/passthrough_auth.py` - Auth injection middleware
- `dose/models/tenant_app.py` - Tenant app tracking model
- `dose/passthrough/handlers/odoo_handler.py` - Odoo passthrough handler (PolySniffer-generated)
- `dose/passthrough/handlers/mattermost_handler.py` - Mattermost passthrough handler (PolySniffer-generated)
- `dose/models/pass_through_endpoint.py` - Endpoint configuration model
- `dose/context_processors.py` - Navigation context processor
- `dose/passthrough/middleware.py` - Main passthrough middleware
- `dose/passthrough/handlers/registry.py` - Handler registry
- `dose/services/odoo_tenant_provisioner.py` - Odoo provisioning service
- `dose/services/mattermost_tenant_provisioner.py` - Mattermost provisioning service
- `dose/management/commands/setup_default_passthrough_endpoints.py` - Production setup command for default endpoints
- `dose/subscription_views.py` - Subscription flow with provisioner wiring

### Changes Made
- Added `starting_uri` field to PassThroughEndpoint model (migration 0043)
- Fixed TenantApp tenant_id column type from bigint to varchar (migration 0044)
- Created PassThroughEndpoint records for Odoo (http://localhost:8069) and Mattermost (http://localhost:8065)
- Created management command `setup_default_passthrough_endpoints` for production endpoint setup
- Renamed from demo-focused naming to production-focused naming

### Files Changed
- `dose/models/pass_through_endpoint.py` - Added starting_uri field
- `dose/migrations/0043_passthroughendpoint_starting_uri.py` - Migration for starting_uri field
- `dose/migrations/0044_alter_tenantapp_tenant_id_to_varchar.py` - Migration for tenant_id type fix
- `dose/management/commands/setup_default_passthrough_endpoints.py` - Production endpoint setup command

### Follow-ups
1. Ensure Odoo and Mattermost services running at configured URLs
2. Test subscription flow with enable_odoo and enable_mattermost
3. Verify Odoo passthrough auto-login and navigation
4. Verify callback data capture for Odoo events
5. Verify Mattermost team creation with tenant slug
6. Verify Mattermost passthrough and town square posting
7. Wire PolySniffer to capture Mattermost chat events for AI adapter triggering
8. Implement AI Adapter using Windsurf API
9. Implement AI Adapter using Grok API
10. Wire passthrough dynamic event handling for 3-way AI conversation (Windsurf + Grok + human/Mattermost)

---

## 2026-04-29 (Session End)
**Status**: Session Complete
**Branch**: main

### Summary
Implemented permanent passthrough infrastructure for Odoo and Mattermost. User clarified this is production behavior (not one-off demo) - users subscribe and have instant access to apps they selected. All infrastructure is now permanent and committed to GitHub.

### Files Changed
- `dose/models/pass_through_endpoint.py` - Added starting_uri field
- `dose/migrations/0043_passthroughendpoint_starting_uri.py` - Migration for starting_uri field
- `dose/migrations/0044_alter_tenantapp_tenant_id_to_varchar.py` - Migration for tenant_id type fix
- `dose/management/commands/setup_default_passthrough_endpoints.py` - Production endpoint setup command (renamed from demo)
- `documentation/COORDINATION_README.md` - Updated coordination log

### Commits
- 95b3b4c: Add permanent passthrough infrastructure for Odoo and Mattermost
- 31a2894: Update coordination log with production passthrough infrastructure changes

---

## 2026-05-01
**Status**: ✅ COMPLETE - BINGO!
**Branch**: main

### Summary
Fixed blank Django admin user edit page on production (Render). The issue was caused by a multi-tenancy schema mismatch where UserProfile objects were in tenant schemas but trying to reference User objects in public schema. When the inline form tried to render, it crashed because the related User wasn't accessible in the tenant schema context.

### Key Fixes
- Fixed `CustomUserAdmin.get_object()` to force `search_path TO public` before querying users
- Added `get_queryset` to `UserProfileInline` to query from public schema and filter inaccessible profiles
- Fixed `UserProfile.__str__` to handle `User.DoesNotExist` gracefully
- Fixed template block inheritance in `base_site.html`

### Files Changed
- `dose/admin.py` - Schema-aware User and UserProfile query handling
- `dose/models/user_profile.py` - Graceful handling of missing user in __str__
- `dose/templates/admin/base_site.html` - Fixed Jazzmin block inheritance
- `dose/tenant_utils.py` - Added tenant debugging logging
- `dose/management/commands/migrate_users_to_public.py` - User migration command
- `dose/management/commands/check_template_loading.py` - Template diagnostics

### Verification
- ✅ User list page loads correctly
- ✅ User edit form displays with all fields
- ✅ Can save changes to users
- ✅ No more `DoesNotExist` errors

### Follow-ups
- Consider moving UserProfile table to public schema for consistency
- Ensure future user creation always happens in public schema
- Document this multi-tenancy pattern to prevent regression

### Commits
- See `documentation/BINGO_Blank_Admin_User_Edit_Fix.md` for full details

---

## 2026-05-01 (Morning Session)
**Status**: In Progress
**Branch**: main

### Summary
Fixed passthrough endpoint visibility and functionality for the current tenant. The passthrough endpoints (Odoo, Mattermost, NextCloud) are now correctly displayed in the Django admin sidebar and functional. Fixed middleware and views to properly query `PassThroughEndpoint` records within tenant schemas by setting `search_path` before database queries.

### Key Fixes
- Modified `setup_default_passthrough_endpoints` command to support tenant schemas with `--tenant-slug` argument
- Added NextCloud endpoint creation to the setup command
- Updated Odoo, Mattermost, NextCloud provisioners to create `PassThroughEndpoint` records in tenant schemas on subscription
- Fixed `admin_views.py` `passthrough_embed_view` to set tenant schema `search_path` before querying endpoints
- Fixed `passthrough/middleware.py` `run_pt_admin_passthrough_core` to set tenant schema `search_path` before querying endpoints
- Changed `URLField` to `CharField` for `endpoint_url` and `api_endpoint` in `PassThroughEndpoint` model to allow internal Docker hostnames
- Added fallback and debug logging to Odoo handler for when HTML body tag extraction fails

### Files Changed
- `dose/management/commands/setup_default_passthrough_endpoints.py` - Added tenant slug argument, NextCloud endpoint, schema-aware creation
- `dose/services/odoo_tenant_provisioner.py` - Added PassThroughEndpoint creation in tenant schema
- `dose/services/mattermost_tenant_provisioner.py` - Added PassThroughEndpoint creation in tenant schema
- `dose/services/nextcloud_tenant_provisioner.py` - Added PassThroughEndpoint creation in tenant schema
- `dose/admin_views.py` - Fixed passthrough view to set tenant schema search_path
- `dose/passthrough/middleware.py` - Fixed middleware to set tenant schema search_path
- `dose/models/pass_through_endpoint.py` - Changed URLField to CharField for Docker hostname support
- `dose/passthrough/handlers/odoo_handler.py` - Added fallback and debug logging for body extraction

### URLs Configured
- Odoo: `https://polysaas-odoo2.onrender.com`
- Mattermost: `https://polysaas-mattermost.onrender.com`
- NextCloud: `http://polysaas-nextcloud:80` (internal Docker)

---

## 2026-05-02 (Morning Session)
**Status**: In Progress
**Branch**: main

### Summary
Extended passthrough infrastructure to all 6 bundled apps (Odoo, Mattermost, NextCloud, Dolibarr, Liferay, WordPress). Created AI WebChat Bridge architecture plan with Sheila's review feedback, and implemented Mattermost Bot skeleton with Kimi + Claude adapters.

### Key Changes
- Extended `setup_default_passthrough_endpoints` command to support all 6 bundled apps
- Fixed `dolibarr_tenant_provisioner.py`, created `liferay_tenant_provisioner.py` and `wordpress_tenant_provisioner.py`
- Created comprehensive AI WebChat Bridge Plan (`documentation/AI_WebChat_Bridge_Plan.md`) — Sheila reviewed
- Implemented `dose/ai_bridge/` package (base, kimi, claude adapters + mattermost bot)

### Status
- ✅ All 6 bundled app provisioners committed and pushed
- ✅ AI WebChat Bridge Plan committed (Sheila reviewed)
- ✅ Kimi + Claude adapters + Mattermost Bot committed
- ⚠️ Odoo passthrough blank — root cause was DB gone (app on cache), NOT code bugs

---

## 2026-05-03 (Early Morning — Laptop)
**Status**: ✅ BINGO
**Branch**: main

### Summary
Fixed Odoo passthrough blank/garbled screen. Odoo login form now renders correctly inside PolySaaS admin shell.

### Root Cause Chain
1. Sidebar URL used `trigger_path` norm instead of `endpoint_url` hostname → middleware lookup always missed
2. No root redirect for hostname triggers → browser hit Odoo `/` returning garbled bytes
3. `brotlicffi` missing from requirements.txt → Render CDN's Brotli-encoded responses decoded as garbled UTF-8
4. `allow_redirects=False` caused 502 on Render → reverted to True
5. **KEY INSIGHT**: Many apparent "code bugs" in previous sessions were actually caused by `polysaas_postgres` DB being gone — app was running on cached session data

### Key Architecture Rule
- Sidebar href = `/pt/admin/<endpoint_url hostname>/`
- Middleware matches endpoint by `endpoint_url__icontains="://<hostname>"` (DB lookup)
- Root path → Django redirect to `/web/login` (browser URL stays correct)
- `allow_redirects=True` for GET, `False` for POST (browser follows post-login redirect to correct URL)
- `brotlicffi==1.1.0.0` in requirements.txt for Brotli decompression

### Files Changed
- `dose/context_processors.py` — sidebar URL from `endpoint_url` hostname
- `dose/passthrough/middleware.py` — endpoint lookup by `endpoint_url` hostname
- `dose/passthrough/handlers/odoo_handler.py` — root redirect to `/web/login`, smarter allow_redirects
- `requirements.txt` — added `brotlicffi==1.1.0.0`
- `documentation/BINGO_Odoo_Passthrough_Login.md` — this session's BINGO doc

### Rollback Note
Rolled back 47 commits to `0616583` (last BINGO). All discarded work saved on `passthrough-wip` branch on GitHub.

### Follow-ups for Next Session
- Test Odoo **post-login** (form submit → session → `/odoo/` apps page)
- Verify Location header rewriting works for post-login redirect
- Test Mattermost passthrough (same hostname approach)
- Re-integrate AI Bridge (Kimi/Claude adapters) from `passthrough-wip` branch
- Re-integrate provisioners for all 6 bundled apps from `passthrough-wip` branch

---

## 2026-05-03 — Odoo DB Disaster Recovery + Infrastructure Hardening

### Status: ✅ BINGO — Odoo healthy, service recovered 7:40 PM

### Branch: main

### Summary
Attempted to reset Odoo admin credentials via Odoo DB manager → the "Delete Database"
operation succeeded (despite showing a 500 error), wiping `polysaas_postgres` which was
shared by BOTH Django (Core) and Odoo. Both services went down.

Recovery steps taken:
- Created `polysaas_postgres` database in PgAdmin (reconnected to Render PostgreSQL)
- PolySaaS-Core redeployment still failing — DATABASE_URL may point to a DIFFERENT
  Render PostgreSQL than where the DB was recreated. Need to verify `DATABASE_URL` host.
- Set `PolySaaS-Odoo2 autoDeployTrigger: off` in render.yaml to prevent Python commits
  from triggering unnecessary Odoo redeployments.
- Identified root cause of shared DB: individual env vars on Odoo2 overrode group
  `ODOO_DB_NAME: odoodb` with `polysaas_postgres` (Django's DB name).

### Files Changed
- `render.yaml` — `PolySaaS-Odoo2 autoDeployTrigger: off`

### CRITICAL Next-Session Actions (do these FIRST)
1. Check `DATABASE_URL` in Render → PolySaaS-Core → Environment — get the DB hostname
2. Connect PgAdmin to THAT specific PostgreSQL host and create `polysaas_postgres` there
3. Manual Deploy PolySaaS-Core — wait for pre-deploy (migrate_all_schemas) to succeed
4. In Render → `polysaas-odoo` env group, set:
   - `ODOO_DB_HOST` = `dpg-d7lple0ebus73e3le4ug-a`
   - `ODOO_DB_USER` = `polysaas_postgres_user`
   - `ODOO_DB_NAME` = `odoodb` (NOT polysaas_postgres — keep them separate!)
   - `ODOO_DB_PASSWORD` = `yTfbrzBFpCpSfLCICemNZUbqnfq1G5yU`
5. Create `odoodb` database in PgAdmin: `CREATE DATABASE odoodb OWNER polysaas_postgres_user;`
6. Remove individual Odoo2 env overrides: `ODOO_DB_NAME`, `ODOO_DB_USER`, `HOST`
   (group values will take over cleanly)
7. Manual Deploy PolySaaS-Odoo2
8. Go to Odoo DB manager, create database with known admin password
9. Test Odoo login via passthrough — verify post-login redirect to apps page

---

## 2026-05-04 (Early Morning — Laptop → Office)
**Status**: IN PROGRESS — env group fixed, deploy pending
**Branch**: main

### Summary
Picked up at office. Odoo was in crash loop due to stale env group values. Fixed `polysaas-odoo` 
environment group to use correct Render PostgreSQL credentials and point to `odoo_prod` DB.

### Actions Completed
- Identified `polysaas-odoo` group had wrong values: `odoodb` (non-existent), `odoouser`, missing host/password
- Updated group values:
  - `DB_NAME` / `ODOO_DB_NAME`: `odoo_prod`
  - `ODOO_DB_USER`: `polysaas_postgres_user`
  - `ODOO_DB_HOST`: `dpg-d7lple0ebus73e3le4ug-a`
  - `ODOO_DB_PASSWORD`: `yTfbrzBFpCpSfLCICemNZUbqnfq1G5yU`
- Committed `render.yaml` changes:
  - Hardcoded `ODOO_DB_NAME=odoo_prod` on service (overrides group if needed)
  - Added `ODOO_AUTO_INIT=1` to force re-initialization (fixes missing `web.login` template)

### Pending (Next Session at Office)
- Wait for PolySaaS-Odoo2 Manual Deploy to complete init
- Verify `/web/login` renders without 500
- Reset admin password via SQL or DB manager
- Test passthrough login end-to-end
- **Remove `ODOO_AUTO_INIT`** from render.yaml after successful init

### Files Changed
- `render.yaml` — hardcoded `ODOO_DB_NAME` and `ODOO_AUTO_INIT` for Odoo2 service

---

## 2026-05-04 (Evening — Condo)
**Status**: PAUSED — 15hr day, new SDLC plan for tomorrow
**Branch**: main

### Summary
Odoo2 still not showing login via passthrough (blank screen on sidebar click). After frustrating 
debug cycle with Render logs, realized current SDLC is backwards: committing infra changes and 
waiting for Render deploy to test passthrough logic is painfully slow.

### New SDLC Rule (Effective Tomorrow)
1. **Develop and test passthrough logic LOCALLY first** — add logging, find errors, fix immediately
2. **Only commit/push to Render after local validation** — minimize Render cycle to final verification
3. **Local Django + local Postgres** for all passthrough development
4. **External services (Odoo, Mattermost, etc.) stay on Render** — accessed via passthrough as designed

### Tomorrow's First Task
Test Odoo passthrough locally:
- `python manage.py runserver`
- Click Odoo sidebar
- Add tracing to `odoo_handler.py` to find blank screen root cause
- Fix locally, verify, then commit/push

### Current Render Status
- PolySaaS-Odoo2: Running but passthrough shows blank (not 500)
- Env group values correct (`odoo_prod`, proper credentials)
- `ODOO_AUTO_INIT` still in YAML (remove after login works)

---

## 2026-05-05 (Evening — Condo)
**Status**: IN PROGRESS — Odoo login working, Mattermost admin lost
**Branch**: main

### Summary
Pulled from GitHub (38 objects from desktop session). Big news: **Odoo passthrough login is working** — apps screen renders after login. The earlier blank screen issue is resolved.

Mattermost admin credentials lost (thought they were `mmadmin` / `PolySaaS2026!` but not working). Recovery options identified:
- `mmctl user list` / `mmctl user change-password` in Render Shell
- `mattermost user create --local --system_admin` in Render Shell  
- Direct SQL on `mattermost` DB in PgAdmin as fallback

### Ultimate Goal (The North Star)
New subscriber → provision apps (Odoo, Mattermost, NextCloud, etc.) → SSO to those apps in the company's name seamlessly.

### Tomorrow's First Task
Recover Mattermost admin credentials, verify Mattermost passthrough login works end-to-end.

---

## 2026-05-06 (Morning — Condo → Office)
**Status**: DONE — Mattermost passthrough working
**Branch**: main

### Summary
Created Django superuser `mmadmin@polysaas.online` / `PolySaaS2026!` for local admin access.

**Mattermost passthrough is LIVE**: Clicking "Mattermost" in the PolySaaS admin sidebar loads the full Mattermost UI inside the passthrough proxy. User can log in with `mikeoliveraz` / `PolySaaS2026!` and sees Town Square, channels, direct messages. The shim correctly rewrites static assets (`/pt/admin/mattermost/static/...`) and API calls.

**Known cosmetic issues (non-blocking):**
- WebSocket banner "Mattermost unreachable" — Render free tier doesn't support WS upgrade; Mattermost falls back to HTTP polling automatically
- Plugin bundles (github, playbooks, nps, calls) return 404 — non-critical, core chat works
- External telemetry CORS errors (`pdat.matterlytics.com`) — unrelated to passthrough

**Pending for future sessions:**
- Auto-login via `MMAUTHTOKEN` injection (requires tenant app `extra_config` with Mattermost credentials)
- Fix plugin static asset routing through proxy
- WebSocket passthrough support (if Render plan supports it)

### Files Changed
- `documentation/COORDINATION_README.md` (this entry)

---

## 2026-05-08 (Morning — Condo → Office)
**Status**: DONE — dashboard fix + Odoo2 deploy recovered
**Branch**: main

### Summary
1. **Fixed Django admin NoReverseMatch**: Added missing `path('dashboard/', dashboard, name='dashboard')` to `dose/urls.py`. The `templates/jazzmin/admin/index.html` references `{% url 'dose:dashboard' %}` but the route was never registered. Committed and pushed.
2. **Odoo2 deploy fixed**: Previous deploy failed because `ODOO_DB_NAME=odoo_prod` but database `odoo_prod` never existed. Changed to `odoodb` in `render.yaml` (which matches the DB initialized earlier). Also updated directly in Render dashboard env vars and triggered manual deploy. Build and deploy succeeded; service is live.
3. **Auto-deploy remains OFF**: All Render services have `autoDeployTrigger: off`. Manual deploys required from dashboard.

### Login Credentials Note
- Default Odoo superuser after `-i base,web` init: `admin / admin` (not `odooAdmin / PolySaaS2026!`)
- `odooAdmin / PolySaaS2026!` is only created by the tenant provisioner when a user subscribes

### Files Changed
- `dose/urls.py` — added missing `dashboard` named route
- `render.yaml` — changed `ODOO_DB_NAME` from `odoo_prod` to `odoodb`
- `documentation/COORDINATION_README.md` (this entry)
