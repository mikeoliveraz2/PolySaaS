# Active Handoff

This file is the canonical startup and end-of-day handoff for PolySaaS.
Every agent (Copilot, Cursor, Windsurf) must read it before work and update it at EOD.

**Date:** 2026-09-16 (Wednesday)  
**Session:** WordPress home SaaS card shots + Founders/legal staging (live edit on polysaas.online)  
**Branch:** main  
**Latest related commit:** `694a6186` (Founders Beta + Mattermost CP BINGO); this push adds WP staging/scripts + live Odoo-shot note  

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

- Restored azure staging quality pass earlier (home copy, Founders, legal, MM/HS card shots), then Migrate Guru direction issues noted.
- **Live only (no remigrate):** inserted Odoo home-card shots on polysaas.online page `1313` using existing media `odoo-cpanel-scaled.png` + `odoo-browser-scaled.png` (`data-polysaas-shots="odoo"`). Mattermost + HubSpot shots already present.
- Repo: WordPress staging HTML/MD under `documentation/website/`, sync helpers `scripts/wp_sync_founders_beta_page.py` + `scripts/wp_sync_legal_pages.py`, capital-raise notes.

## BINGO still valid

- Founders Beta $10 + Mattermost CP — `BINGO_FOUNDERS_BETA_AND_MATTERMOST_CP_2026-09-16.md` (`694a6186`)
- Hostinger Mattermost passthrough — `BINGO_HOSTINGER_MM_PASSTHROUGH_2026-09-13.md`
- Hostinger Odoo HTTPS login — `BINGO_HOSTINGER_ODOO_HTTPS_LOGIN_2026-09-12.md`

## Next actions

1. Hard-refresh Mattermost CP to confirm wireframe gone; smoke-test New contact / New sale bookmarks.
2. Dokploy: confirm live Stripe env vars deployed; optional $1 Founders smoke charge.
3. Optional: sync azure staging home Odoo shots to match live (edit azure only — no Migrate Guru unless explicitly requested).
4. Rotate Odoo admin password (prior ops item).

## Ops reminder

Django on Hostinger is **image-baked** — after pushing, Dokploy must **Rebuild** (not only Deploy) when code changes. Env-only Stripe updates need container recreate with new env.
