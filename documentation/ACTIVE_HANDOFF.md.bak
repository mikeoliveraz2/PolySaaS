# Active Handoff

This file is the canonical startup and end-of-day handoff for PolySaaS.
Every agent (Copilot, Cursor, Windsurf) must read it before work and update it at EOD.

**Date:** 2026-09-12 (Saturday)  
**Session:** Hostinger + Dokploy — Odoo HTTPS login **BINGO**  
**Branch:** main  

## Live infra

| Item | Value |
|------|-------|
| Provider | Hostinger VPS |
| Orchestration | **Dokploy** |
| VPS IP | `187.53.138.235` |
| Domain | `prod-polysaas.cloud` |
| Hosts | `app` / `mm` / `odoo`.prod-polysaas.cloud |
| DNS A records | **DONE** — all three → `187.53.138.235` |
| SSH (`id_ed25519_hostinger`) | Laptop still saw Permission denied earlier; use Dokploy UI when SSH fails |

## BINGO this session

- **Hostinger Odoo HTTPS login** — `documentation/BINGO_HOSTINGER_ODOO_HTTPS_LOGIN_2026-09-12.md`
- Verified: browser login → Odoo Apps; curl GET→POST → `303 /odoo`
- Frozen: `deploy/hostinger/docker-compose.yml`, `odoo-nginx.conf`, `odoo.proxy.conf`

## Also completed (not separate BINGO)

- Django core on Hostinger: migrate, superuser, tenant/`olient` bootstrap (earlier same day)
- Odoo DB init (`odoo -i base`), `web.base.url` = `https://odoo.prod-polysaas.cloud`

## Next actions

1. Rotate Odoo admin password (bootstrap password was temporary).
2. Wire PolySaaS passthrough to in-compose `http://odoo:8069`.
3. Mattermost public routing / health on `mm.prod-polysaas.cloud`.
4. Confirm laptop SSH to VPS if needed for ops outside Dokploy.

## Prior bingo still valid

- Slack / Mattermost / HubSpot → Odoo (`newpolysaascontact` + HubSpot FlowLink)
- Latest HubSpot bingo: `11a0d627`
- Font/theme toggle bingo: `1dcca3bd`
