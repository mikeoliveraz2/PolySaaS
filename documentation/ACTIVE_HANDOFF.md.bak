# Active Handoff

This file is the canonical startup and end-of-day handoff for PolySaaS.
Every agent (Copilot, Cursor, Windsurf) must read it before work and update it at EOD.

**Date:** 2026-09-19 (Saturday)  
**Session:** Sidebar Browse+CP unit + Odoo provision Hostinger wiring  
**Branch:** main  

## Live infra

| Item | Value |
|------|-------|
| Provider | Hostinger VPS |
| Orchestration | **Dokploy** |
| VPS IP | `187.53.138.235` |
| Domain | `prod-polysaas.cloud` |
| Hosts | `app` / `mm` / `odoo`.prod-polysaas.cloud |
| WordPress (marketing) | **polysaas.online** |

## Completed this session

- **WP:** Sign Up / `/dose/subscribe/` → `https://app.prod-polysaas.cloud/dose/subscribe/`
- **Sidebar (owner-approved):** Browse icon + Control Panel are **one unit** — always both visible; ready = clickable; not ready = dimmed / non-clickable. Shela destinations unchanged (icon→Browse, button→CP).
- **Hostinger compose:** Django now gets `ODOO_SHARED_URL` (default `http://odoo:8069`), `ODOO_SHARED_DB`, `ODOO_MASTER_PASSWORD`, plus `MATTERMOST_ADMIN_TOKEN` passthrough.
- **odoo.proxy.conf:** `admin_passwd = admin` so DB manager matches `ODOO_MASTER_PASSWORD` default.

## Why Founders Odoo looked broken

Provision Step 1 created PassThroughEndpoint (icon). Step 2 hit `localhost:8086` inside Django → failed → TenantApp not `active` → CP link was hidden (unit bug). Yesterday’s working Odoo was already `active`.

## Next (Hostinger ops — after push)

1. Dokploy Environment: ensure `ODOO_SHARED_URL=http://odoo:8069` (compose default also works after Rebuild).
2. **Rebuild** Django image (not Deploy-only) so templates + compose env bake in.
3. Open Terminal on **django** container:
   ```bash
   python manage.py repair_tenant_odoo polysaasonline
   ```
   (If slug differs, list tenants first. Pass `--email` if `odoo_login` missing.)
4. Hard-refresh admin — Odoo unit should show Control Panel; when `active`, both clickable.

## Authority

No sidebar design changes without Michael/Shela explicit approval. Browse+CP unit rule is owner-mandated.

## BINGO still valid

- Founders Beta $10 + Mattermost CP — `694a6186`
- Hostinger MM passthrough / Odoo HTTPS login BINGOs unchanged
