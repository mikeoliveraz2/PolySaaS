# PolySaaS Coordination Log

**RULE:** Every session must update this file with enough context for the next Windsurf instance to pick up immediately — no re-explaining needed. Include: what changed, why, what was suspected, and detailed remaining steps.

---

## 2026-04-30 (Morning — Traefik + Render Blueprint sessions)
**Status**: Traefik routing working. Nextcloud deployment pending. Git conflict unresolved.
**Branch**: main
**Latest pushed commit**: `a619871` (Add PostgreSQL database for Nextcloud)
**Local unpushed commit**: `f6ae93d` (Remove duplicate render.yaml from traefik-stack directory) — push blocked by non-fast-forward

### What Was Accomplished
1. **Traefik routing fully working** for:
   - `https://production.polysaas.online` → PolySaaS-Core (Django)
   - `https://production.polysaas.online/odoo` → PolySaaS-Odoo2
   - `https://production.polysaas.online/mattermost` → PolySaaS-Mattermost

2. **Root causes fixed (in order):**
   - Traefik routing config was in `traefik.render.yml` (static config) — moved to `dynamic.yml` (file provider loads this)
   - Routers used `websecure` entrypoint — switched to `web` (Render terminates SSL, forwards HTTP on port 80)
   - `passHostHeader: true` (default) caused Render edge to 403 — set `passHostHeader: false` per service
   - `DisallowedHost` because Render uses `mysite.settings_render` not `mysite.settings` — fixed in `settings_render.py`
   - `ALLOWED_HOSTS` env var override — added hard-coded append block to always include `.polysaas.online`
   - `CSRF_TRUSTED_ORIGINS` missing production URLs — added defaults in `settings_render.py`

3. **Nextcloud added to Blueprint** (`render.yaml`) with PostgreSQL database (`PolySaaS-Nextcloud-DB`)

4. **Duplicate Blueprint deleted** from Render Dashboard (kept `-BP`, deleted `-Blueprint`) — both pointed to same `render.yaml`

5. **`traefik-stack/render.yaml` deleted locally** — commit `f6ae93d` exists locally but not pushed (git conflict)

### What Remains (Detailed)

#### IMMEDIATE — Fix Git Conflict
```
git pull origin main  # pulls remote changes made from home laptop
git push origin main  # pushes local commit f6ae93d
```
If merge conflict occurs, keep both sets of changes.

#### NEXT — Nextcloud Deployment
1. In Render Dashboard → Blueprint → Sync/Apply (PolySaaS-BP)
2. Fill secrets when prompted:
   - `POSTGRES_PASSWORD` (for PolySaaS-Nextcloud-DB)
   - `NEXTCLOUD_ADMIN_USER` (e.g. `admin`)
   - `NEXTCLOUD_ADMIN_PASSWORD`
   - `NEXTCLOUD_BASE_URL` (in polysaas-bundled-apps group) → `https://production.polysaas.online/nextcloud`
   - `NEXTCLOUD_SERVICE_TOKEN` (can be blank for now)
3. Wait for PolySaaS-Nextcloud to show **Live**
4. Get the service URL (e.g. `https://polysaas-nextcloud.onrender.com`)
5. Add Traefik routing in `traefik-stack/dynamic.yml` (same pattern as Mattermost)

#### THEN — Remaining Traefik Routes
Add to `traefik-stack/dynamic.yml` once service URLs are confirmed:
- **WordPress**: need URL from Render → PolySaaS-WordPress service
- **Liferay**: need URL from Render → PolySaaS-Liferay service
- **PolySysMon**: need to uncomment in `render.yaml` first, then get URL
- **Dolibarr**: need to uncomment in `render.yaml` first, then get URL

#### THEN — Uncomment in render.yaml
- **PolySysMon**: `PolySaaS-PolySysMon-Worker` (existing Docker app) — uncomment commented block
- **Dolibarr**: `PolySaaS-Dolibarr` (tuxgasy/dolibarr:latest image) — uncomment commented block

#### FUTURE — Not yet developed
- **AI As Peers**: Python worker utility — to be designed and built
- **Apps As Peers**: Python worker utility — to be designed and built

### Unresolved Bug (from home laptop session)
User was debugging "edit user in admin interface not displaying" on dev instance.
- **What**: Edit User page in admin not displaying correctly
- **Where**: Dev instance (local), Django admin
- **Status**: Was being debugged, fixes committed from home laptop — next session needs to `git pull` and check what changed

### Key File Locations
| File | Purpose |
|------|---------|
| `traefik-stack/dynamic.yml` | Traefik routing rules (routers, services, middlewares) |
| `traefik-stack/traefik.render.yml` | Traefik static config (entrypoints, providers) |
| `traefik-stack/Dockerfile` | Builds Traefik image, copies `traefik.render.yml` + `dynamic.yml` |
| `mysite/settings_render.py` | Django settings used on Render (NOT `settings.py`) |
| `render.yaml` | Main Render Blueprint — all services defined here |

### Traefik Routing Pattern (for adding new services)
```yaml
# In traefik-stack/dynamic.yml

routers:
  my-service:
    rule: "Host(`production.polysaas.online`) && PathPrefix(`/mypath`)"
    service: my-service
    entryPoints:
      - web                    # Always 'web' not 'websecure' — Render terminates SSL
    middlewares:
      - strip-mypath

services:
  my-service:
    loadBalancer:
      passHostHeader: false    # Always false — Render edge needs its own hostname
      servers:
        - url: https://polysaas-myservice.onrender.com

middlewares:
  strip-mypath:
    stripprefix:
      prefixes:
        - /mypath
      forceSlash: false
```

---

## 2026-04-29 (Passthrough / AI Adapter session)
**Status**: Research complete, implementation not started
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
- `dose/middleware/passthrough_auth.py`
- `dose/models/tenant_app.py`
- `dose/passthrough/handlers/odoo_handler.py`
- `dose/passthrough/handlers/mattermost_handler.py`
- `dose/models/pass_through_endpoint.py`
- `dose/context_processors.py`
- `dose/passthrough/middleware.py`
- `dose/passthrough/handlers/registry.py`
- `dose/services/odoo_tenant_provisioner.py`
- `dose/services/mattermost_tenant_provisioner.py`
- `dose/management/commands/setup_demo_sync.py`

### Remaining Steps
1. Check if PassThroughEndpoint records exist for Odoo and Mattermost
2. Create PassThroughEndpoint records if missing
3. Ensure TenantApp records exist and are marked active
4. Wire PolySniffer to capture Mattermost chat events for AI adapter triggering
5. Implement AI Adapter using Windsurf API
6. Implement AI Adapter using Grok API
7. Wire passthrough dynamic event handling for 3-way AI conversation (Windsurf + Grok + human/Mattermost)
