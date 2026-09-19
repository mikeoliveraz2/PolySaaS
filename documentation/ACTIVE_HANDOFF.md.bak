# Active Handoff

This file is the canonical startup and end-of-day handoff for PolySaaS.
Every agent (Copilot, Cursor, Windsurf) must read it before work and update it at EOD.

**Date:** 2026-09-17 (Thursday)  
**Session:** Fix Founders promo subscribe CTAs (buttons + `/subscribe/` redirect)  
**Branch:** main  

## Live infra

| Item | Value |
|------|-------|
| Provider | Hostinger VPS |
| Orchestration | **Dokploy** |
| VPS IP | `187.53.138.235` |
| Domain | `prod-polysaas.cloud` |
| Hosts | `app` / `mm` / `odoo`.prod-polysaas.cloud |
| WordPress (marketing) | **polysaas.online** (edit target). Azure-nightingale is staging only — do not remigrate unless asked. |

## Completed this session

- Live WP `/newpromo/` + `/founders-beta-circle/`: CTAs are **buttons** pointing at `https://app.prod-polysaas.cloud/dose/subscribe/` (works now).
- Repo: `mysite/urls.py` adds `/subscribe/` → `/dose/subscribe/` redirect (needs **Dokploy Rebuild** before short URL stops 404ing).
- Staging HTML under `documentation/website/` updated to match.

## BINGO still valid

- Founders Beta $10 + Mattermost CP — `BINGO_FOUNDERS_BETA_AND_MATTERMOST_CP_2026-09-16.md` (`694a6186`)
- Hostinger Mattermost passthrough — `BINGO_HOSTINGER_MM_PASSTHROUGH_2026-09-13.md`
- Hostinger Odoo HTTPS login — `BINGO_HOSTINGER_ODOO_HTTPS_LOGIN_2026-09-12.md`

## Next actions

1. **Dokploy Rebuild** Django image so `/subscribe/` redirects to `/dose/subscribe/`.
2. Hard-refresh Mattermost CP; smoke-test New contact / New sale bookmarks.
3. Optional: $1 Founders smoke charge after Stripe env confirmed.
4. Rotate Odoo admin password (prior ops item).

## Ops reminder

Django on Hostinger is **image-baked** — after pushing, Dokploy must **Rebuild** (not only Deploy) when code changes. Env-only Stripe updates need container recreate with new env.
