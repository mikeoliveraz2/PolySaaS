# Active Handoff

This file is the canonical startup and end-of-day handoff for PolySaaS.
Every agent (Copilot, Cursor, Windsurf) must read it before work and update it at EOD.

**Date:** 2026-09-13 (Sunday)  
**Session:** Hostinger + Dokploy — Mattermost passthrough embed **BINGO**  
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
| SSH (`id_ed25519_hostinger`) | Prefer Dokploy UI / terminal when SSH fails |

## BINGO this session

- **Hostinger Mattermost passthrough (Town Square)** — `documentation/BINGO_HOSTINGER_MM_PASSTHROUGH_2026-09-13.md`
- Code commits: `c3e8cfa6` (MM healthcheck), `c31479a3` / `7201b356` (static proxy rewrite), `cec81578` (`matches_endpoint` for `mm.*`)
- Verified: `/pt/admin/mm.prod-polysaas.cloud/` → Town Square + composer in admin embed
- Frozen: `dose/passthrough/handlers/mattermost_handler.py`

## Prior bingo still valid

- Hostinger Odoo HTTPS login — `89aedefa` / `BINGO_HOSTINGER_ODOO_HTTPS_LOGIN_2026-09-12.md`
- Slack / Mattermost / HubSpot → Odoo; HubSpot `11a0d627`; font/theme `1dcca3bd`

## Local WIP (not in this bingo)

- Subscribe BYOL edits still uncommitted: `subscribe.html`, `subscription_views.py`, `serializers.py`, `settings.py` (+ bak)

## Next actions

1. Rotate Odoo admin password (bootstrap password was temporary).
2. Wire PolySaaS Odoo passthrough to in-compose `http://odoo:8069` (same Hostinger playbook as MM).
3. Optional: point MM `endpoint_url` back to `http://mattermost:8065` once proxy-only browser paths are trusted end-to-end.
4. Confirm laptop SSH to VPS if needed for ops outside Dokploy.
5. Commit/push subscribe WIP when ready (separate from this bingo).

## Ops reminder

Django on Hostinger is **image-baked** — after pushing handler fixes, Dokploy must **Rebuild** (not only Deploy). Use **Git** provider, not the unconfigured GitHub App tab.
