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
Fixed passthrough endpoint visibility and functionality for the corent tenant. The passthrough endpoints (Odoo, Mattermost, NextCloud) are now correctly displayed in the Django admin sidebar and functional. Fixed middleware and views to properly query `PassThroughEndpoint` records within tenant schemas by setting `search_path` before database queries.

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

### Status
- ✅ Passthrough endpoints visible in sidebar for corent tenant
- ✅ Endpoint queries work correctly in tenant schemas
- ✅ Docker/internal hostnames now accepted
- ⚠️ Odoo display shell shows blank content (needs further debugging)
- ⚠️ Mattermost and NextCloud need testing

### Follow-ups
1. Debug Odoo display shell blank content issue
2. Test Mattermost passthrough functionality
3. Test NextCloud passthrough functionality
4. Verify auto-login works when TenantApp is active
5. Document tenant schema search_path pattern for future reference
