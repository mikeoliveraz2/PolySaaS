# PolySaaS Coordination Log

This document tracks session activity across machines (laptop/desktop) for synchronization.

---

## 2026-04-29
**Status**: In Progress
**Branch**: main

### Summary
Explored existing passthrough infrastructure to understand how to wire Odoo and Mattermost for dynamic event orchestration with AI adapters. Confirmed both Odoo and Mattermost passthrough handlers already exist and are PolySniffer-generated for dynamic event capture during passthrough sessions.

### Key Findings
- **PassthroughAuthMiddleware**: Injects auth headers/JWT on `/pt/` paths with tenant info (tenant_slug, tenant_name)
- **OdooPassthroughHandler**: Comprehensive handler with display shell, auto-login via JSON-RPC, path rewriting, WebSocket support
- **MattermostPassthroughHandler**: Comprehensive handler with display shell, auto-login via MMAUTHTOKEN, WebSocket/fetch/XHR patching
- **Handler Registry**: Both handlers registered with trigger_path matching
- **PassThroughEndpoint model**: Stores endpoint configuration (trigger_path, endpoint_url, menu integration)
- **TenantApp model**: Tracks which apps are provisioned per tenant (odoo, mattermost, nextcloud, etc.)
- **setup_demo_sync.py**: Shows pattern for creating Odoo PassThroughEndpoint
- **Tenant provisioners**: Both odoo_tenant_provisioner.py and mattermost_tenant_provisioner.py exist

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
- `dose/management/commands/setup_demo_sync.py` - Demo setup command with Odoo endpoint creation

### Follow-ups
1. User will check if PassThroughEndpoint records exist for Odoo and Mattermost
2. Create PassThroughEndpoint records if missing
3. Ensure TenantApp records exist and are marked active
4. Wire PolySniffer to capture Mattermost chat events for AI adapter triggering
5. Implement AI Adapter using Windsurf API
6. Implement AI Adapter using Grok API
7. Wire passthrough dynamic event handling for 3-way AI conversation (Windsurf + Grok + human/Mattermost)
