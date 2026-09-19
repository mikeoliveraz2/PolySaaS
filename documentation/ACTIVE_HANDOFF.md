# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-19 (Saturday)
**Session:** Mattermost Browse 404 — search_path clobber
**Branch:** main

## Done
- Hostinger tenant for PolySaaS Online is schema `polysaas` (not polysaasonline).
- Odoo provisioned for `polysaas` (active + Control Panel).
- Sidebar Browse+CP unit; ODOO_SHARED_URL wiring.
- `recover_mattermost_admin_token` + django `MATTERMOST_DB_*`; MM provisioned for polysaasadmin.
- **Root cause of Browse "No enabled PassThroughEndpoint with slug mattermost":**
  `PassthroughAuthMiddleware._inject_app_token` set `search_path` to `public`
  on `/pt/admin/mattermost/`, so PT core looked up the endpoint in the wrong
  schema. Fixed to query `TenantApp` in the tenant schema and keep search_path.
- **Reinforced owner rule across agent sync files:** No tenant-owned data should
  ever be stored in `public`; no `tenant_id` multi-tenancy in shared tables.
  Enforced via `scripts/check_agent_sync.py` phrases.

## Next (Hostinger)
1. Commit/push `dose/middleware/passthrough_auth.py` fix; Dokploy **Rebuild** django.
2. Hard-refresh admin → click Mattermost logo (Browse) — expect Town Square, not 404.
3. Optional: Dokploy persist `MATTERMOST_ADMIN_TOKEN`; change temp MM admin password.
4. If Browse still 404 after rebuild: in django shell, list/create
   `PassThroughEndpoint(slug='mattermost')` in schema `polysaas`.
