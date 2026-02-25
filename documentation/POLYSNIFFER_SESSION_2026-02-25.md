# PolySniffer Session — February 25, 2026

## Summary

Successfully ran PolySniffer live capture against both **Nextcloud** and **Odoo** on the local dev environment. All traffic captured in real-time via the Chrome extension two-tab architecture.

## Endpoints Tested

### Nextcloud (ID=15)
- **URL**: `http://127.0.0.1:8888/`
- **Captures**: 400+ requests including login POST, dashboard GETs, CSS/JS assets, text session pushes
- **Status**: Working perfectly

### Odoo (ID=13)
- **URL**: `http://localhost:8069` (updated from `http://odoo.polysaas.online:8069` which didn't resolve)
- **Captures**: Successfully captured Odoo traffic
- **Note**: Admin password was reset to `admin` for `mikeoliveraz@gmail.com` via direct DB update (Odoo Docker has no mail server for password reset emails)

## Endpoint URL Fixes

Three endpoints in the `olient` tenant had non-resolving domain names. Updated to localhost:

| Endpoint | Old URL | New URL |
|----------|---------|---------|
| Odoo (ID=13) | `http://odoo.polysaas.online:8069` | `http://localhost:8069` |
| Dolibarr (ID=16) | `http://dolibarr.polysaas.online:8889/` | `http://localhost:8889/` |
| Monitor Logger (ID=12) | `http://monitorlogger.com:5000` | `http://localhost:5000` |

## Infrastructure Changes

- **PassThroughEndpoint Swagger API** — full CRUD at `/dose/api/passthroughendpoints/` with computed `proxy_url`, `admin_url`, `polysniffer_url` fields
- **go.ps1 morning sync** — pull + commit + push before backup, ensuring both office and laptop machines stay synced
- **Process Rules 4 & 5** — pull-commit-push sequence and morning sync codified

## Screenshots

Saved in `dose/website/staging/wp-content/uploads/`:
- Nextcloud dashboard from PolySniffer
- PolySniffer Live Capture — login capture
- PolySniffer Live Capture — browsing capture
- Endpoint list with PolySniffer Analysis buttons
- Odoo capture and admin views
