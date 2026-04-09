# BINGO — Odoo + Dolibarr Passthrough Regression Green

**Date:** 2026-04-09
**Certified by:** Michael (manual test)
**Part of:** Full passthrough regression (Mattermost → Nextcloud → Odoo → Dolibarr)

---

## Odoo

| Item | Result |
|------|--------|
| URL | `/pt/admin/odoo/` |
| UI loads | ✅ Full Odoo Apps dashboard rendered |
| Navigation | ✅ Apps module, sidebar, module switching all work |
| Console errors | None blocking |
| Handler | `dose/passthrough/handlers/odoo_handler.py` (display shell, unchanged) |

**Status: GREEN on first pass — no regression from Nextcloud refactor.**

---

## Dolibarr

| Item | Result |
|------|--------|
| URL | `/pt/admin/dolibarr/` |
| Upstream | `http://localhost:8889/` (tuxgasy/dolibarr Docker, port 8889) |
| Credentials | admin / admin |
| UI loads | ✅ Dolibarr 19.0.2 Setup page rendered inside PolySaaS shell |
| Navigation | ✅ Sidebar clicks (My Dashboard, Setup sections) load correctly |
| CSS/styling | ⚠️ Needs polish — theme assets not rewritten yet |
| Handler | Generic passthrough (no dedicated `dolibarr_handler.py` yet) |

**Status: FUNCTIONAL GREEN — loads, navigates, logs in. Style polish deferred.**

---

## Notes

- Dolibarr is started separately: `docker compose -f docker-compose.demo-sync.yml up -d dolibarr-db dolibarr`
- `.\go` does **not** start Dolibarr; manual start required until go scripts are extended
- `PassThroughEndpoint.endpoint_url` must be `http://localhost:8889/` in olient schema
- Style fix for Dolibarr = future `dolibarr_handler.py` with `/theme/` and `/public/` asset rewriting (same playbook as Nextcloud handler)

---

## Regression Summary (as of 2026-04-09)

| Service | Status |
|---------|--------|
| Mattermost | ✅ GREEN (full UI + chat) |
| Nextcloud | ✅ GREEN (dashboard, navigation, login — style polish pending) |
| Odoo | ✅ GREEN (full UI, first pass) |
| Dolibarr | ✅ GREEN (functional — style pending) |
| WordPress | ⬜ Not yet tested this session |
| PolySysMon | ⬜ Not yet tested this session |
