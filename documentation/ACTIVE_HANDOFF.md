# Active Handoff

This file is the canonical startup and end-of-day handoff for PolySaaS.
Every agent (Copilot, Cursor, Windsurf) must read it before work and update it at EOD.

**Date:** 2026-09-19 (Saturday)  
**Session:** Marketing subscribe redirects + sidebar UX authority clarification  
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

- **WP public path to subscribe (live polysaas.online):**
  - Nav + home Sign Up CTAs → `https://app.prod-polysaas.cloud/dose/subscribe/`
  - `/sign-up/` and `/dose/subscribe/` pages redirect to that app URL
- **Sidebar:** intentional Shela split remains (commit `6d936312`): icon → Browse (new tab); **Control Panel** link → endpoint home. An unauthorized agent attempt to remove the CP link was **reverted**; `.bak` synced to match current HTML.
- Cleaned untracked `documentation/website/_tmp_*` / `_inj_*` scratch files (not committed).

## Authority note (production)

Passthrough sidebar Browse + Control Panel split was authorized by **Shela** (2026-09-06). Do **not** change frozen admin sidebar UX without Michael/Shela explicit approval. All production code changes require approval first.

## BINGO still valid

- Founders Beta $10 + Mattermost CP — `BINGO_FOUNDERS_BETA_AND_MATTERMOST_CP_2026-09-16.md` (`694a6186`)
- Hostinger Mattermost passthrough — `BINGO_HOSTINGER_MM_PASSTHROUGH_2026-09-13.md`
- Hostinger Odoo HTTPS login — `BINGO_HOSTINGER_ODOO_HTTPS_LOGIN_2026-09-12.md`

## Next actions

1. Finish Odoo/Mattermost provision for Founders tenant (PolySaaS Online) so tiles are `active` (Control Panel appears / clickable). Wire `ODOO_SHARED_URL=http://odoo:8069` + `MATTERMOST_ADMIN_TOKEN` in Dokploy if still missing.
2. Dokploy **Rebuild** only when code changes need baking (sidebar HTML unchanged vs last ship for CP split).
3. Optional: $1 Founders smoke after Stripe confirmed.

## Ops reminder

Django on Hostinger is **image-baked** — after pushing, Dokploy must **Rebuild** (not only Deploy) when code changes. Env-only updates need container recreate with new env.
