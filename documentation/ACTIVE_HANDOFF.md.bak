# Active Handoff

This file is the canonical startup and end-of-day handoff for PolySaaS.
Every agent (Copilot, Cursor, Windsurf) must read it before work and update it at EOD.

**Date:** 2026-09-16 (Tuesday)  
**Session:** Founders Beta $10 + Stripe live + Mattermost Control Panel (no wireframe) **BINGO**  
**Branch:** main  

## Live infra

| Item | Value |
|------|-------|
| Provider | Hostinger VPS |
| Orchestration | **Dokploy** |
| VPS IP | `187.53.138.235` |
| Domain | `prod-polysaas.cloud` |
| Hosts | `app` / `mm` / `odoo`.prod-polysaas.cloud |

## BINGO this session

- **Founders Beta $10/mo (6 months) + Mattermost CP no-wireframe** — `documentation/BINGO_FOUNDERS_BETA_AND_MATTERMOST_CP_2026-09-16.md`
- Subscribe: exclusive Founders tier locks other options; fee fixed at $10; Stripe live keys in gitignored `.env` / Hostinger `.env` + `.env.enc`
- Mattermost Control Panel: purple Slack wireframe removed; header + orch bar restored; New contact / New sale via bookmarks

## Prior bingo still valid

- Hostinger Mattermost passthrough — `BINGO_HOSTINGER_MM_PASSTHROUGH_2026-09-13.md`
- Hostinger Odoo HTTPS login — `BINGO_HOSTINGER_ODOO_HTTPS_LOGIN_2026-09-12.md`

## Next actions

1. Hard-refresh Mattermost CP to confirm wireframe gone; smoke-test New contact / New sale bookmarks.
2. Dokploy: confirm live Stripe env vars deployed; optional $1 Founders smoke charge.
3. Update polysaas.online blog Founders copy ($100 → $10/mo) once `.env.wordpress` is available.
4. Rotate Odoo admin password (prior ops item).

## Ops reminder

Django on Hostinger is **image-baked** — after pushing, Dokploy must **Rebuild** (not only Deploy) when code changes. Env-only Stripe updates need container recreate with new env.
