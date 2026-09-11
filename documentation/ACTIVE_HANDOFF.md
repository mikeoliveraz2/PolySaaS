# Active Handoff

This file is the canonical startup and end-of-day handoff for PolySaaS.
Every agent (Copilot, Cursor, Windsurf) must read it before work and update it at EOD.

**Date:** 2026-09-12 (Saturday)  
**Session:** Hostinger + Dokploy — domain retarget  
**Branch:** main  

## Live infra

| Item | Value |
|------|-------|
| Provider | Hostinger VPS |
| Orchestration | **Dokploy** |
| VPS IP | `187.53.138.235` |
| Domain | `prod-polysaas.cloud` |
| Hosts | `app` / `mm` / `odoo`.prod-polysaas.cloud |
| SSH (`id_ed25519_hostinger`) | **Not authorized yet** on VPS |

## Completed (repo)

- [`deploy/hostinger/docker-compose.yml`](../deploy/hostinger/docker-compose.yml) adapted for **Dokploy**:
  - Removed local Traefik service (Dokploy owns TLS)
  - External `dokploy-network` + internal `polysaas-hostinger`
  - No `container_name`
  - Hostnames → `*.prod-polysaas.cloud`
- Scripts / runbook / `.env.example` updated for new domain

## Next (operator)

1. Authorize laptop SSH public key on VPS / Dokploy
2. DNS A records for `app`/`mm`/`odoo`.prod-polysaas.cloud → `187.53.138.235`
3. Create Dokploy Compose app from `deploy/hostinger/docker-compose.yml` + filled env
4. Migrate data + retarget Slack/HubSpot → `https://app.prod-polysaas.cloud/...`
5. Smoke tests

## Prior bingo still valid

- Slack / Mattermost / HubSpot → Odoo (`newpolysaascontact` + HubSpot FlowLink)
- Latest HubSpot bingo: `11a0d627`
