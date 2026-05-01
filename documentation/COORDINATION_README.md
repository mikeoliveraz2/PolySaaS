# PolySaaS Coordination Log

This document tracks session activity across machines (laptop/desktop) for synchronization.

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

## 2026-04-30
**Status**: Session Complete
**Branch**: main

### Objective
Fix blank admin change_form (user edit + all model update forms) on production (Render). Same code worked on dev.

### Root Cause 1 — Django cached.Loader + multi-level template inheritance
When `DEBUG=False`, Django auto-wraps template loaders in `cached.Loader`. This mis-resolves `{{ block.super }}` in deep multi-level template inheritance chains (model `change_form.html` → `jazzmin/change_form.html` → `dose/base_site.html` → `jazzmin/base.html`), producing empty `page_content` for all admin change_form views. `change_list` was unaffected (simpler inheritance, no `block.super` for content). Dev used `DEBUG=True` which does not apply `cached.Loader`.

**Fix**: Replaced `APP_DIRS: True` with explicit uncached loaders in `mysite/settings.py` TEMPLATES config.

### Root Cause 2 — Tenant schema shadowing public.auth_user
`SessionTenantMiddleware` sets `SET search_path TO "<tenant_schema>", public`. Django runs migrations into each tenant schema, creating a local copy of `auth_user` in tenant schemas. When `BaseUserAdmin.get_object()` ran `User.objects.get(pk=N)`, Postgres resolved it against the tenant schema copy (which had different/missing rows), raising `DoesNotExist` for all users.

**Fix**: Added `_force_public_schema()` to `CustomUserAdmin` in `dose/admin.py`, called in `get_queryset`, `get_object`, `save_model`, `delete_model`.

### Architecture Rule (user-stated, repeated)
`public` schema is SHARED — not for any specific tenant. Only these belong in public:
- `auth_user`, `dose_tenant`, `dose_userprofile`, `dose_usertenantmembership`, subscriptions, site config
- Everything else belongs in per-tenant schemas

Tenant migrations should NOT create `auth_user` copies in tenant schemas. Long-term fix: audit migrate targets per app. Short-term: `_force_public_schema()` guards on affected ModelAdmins.

### Files Changed
- `mysite/settings.py` — disable cached.Loader (explicit uncached filesystem + app_directories loaders)
- `dose/admin.py` — `CustomUserAdmin._force_public_schema()` for all User admin DB operations
- `templates/admin/auth/user/change_form.html` — User change_form override (belt-and-suspenders fallback if inheritance still fails)

### Commits
- d427bc3: fix(templates): disable cached.Loader to fix block.super failure in change_form views on prod
- 5d1a8e1: fix(admin): force public schema for User admin queries — auth_user shadowed by tenant schema copy

### Pending Follow-ups
1. Test `/admin/auth/user/1/change/` on production — should now show full edit form
2. Test other models' change_form pages on production
3. Long-term: audit which Django apps migrate into tenant schemas vs public-only
4. Apply `_force_public_schema` to Tenant admin and other public-only ModelAdmins
5. After admin bug confirmed fixed, proceed to passthrough integration (Odoo + Mattermost)
