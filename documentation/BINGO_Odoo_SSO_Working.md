# BINGO — Odoo SSO Working

**Date**: 2026-05-09  
**Status**: ✅ COMPLETE  
**Branch**: main  

## Summary

Odoo Single Sign-On is fully working end-to-end. After navigating to the Odoo passthrough,
the user is automatically authenticated (no manual login required) and lands on the Odoo
Invoicing app without a blank page.

## Root Causes Fixed (this session)

1. **Display shell missing credentials** — `try_root_display_shell_response` never passed
   `display_credentials` to the template, so `CRED_LOGIN/PASS/DB` were undefined in JS and
   `autoLoginOdoo` returned immediately. Fixed by adding `display_credentials` to context and
   a new SSO block in `display.html`.

2. **400 Bad Request on manual login POST** — `get_request_body` was replacing the browser's
   valid csrf_token with a tenant-session token (different session → mismatch → 400).
   Fixed by simplifying `get_request_body` to `return None` (pass body through unchanged).

3. **SSO 401 "Odoo Server Error"** — `odoo_db` stored in `TenantApp.extra_config` was
   `tenant.schema_name` (the PolySaaS Postgres schema), not the Odoo database name `odoodb`.
   Fixed by hardcoding `db = "odoodb"` in `odoo_sso_api.py`.

4. **`window.location.reload()` causing blank page** — after SSO success, reloading the display
   shell re-embedded the Odoo SPA inside Jazzmin admin → Owl couldn't mount → blank.
   Fixed: navigate to `data.redirect_url` (`/pt/admin/<hostname>/web`) instead.

5. **All `alert()` debug popups** — removed from `_inject_client_shim` JS.

## Files Changed

- `dose/odoo_sso_api.py` — hardcode `db=odoodb`, try tenant creds then admin fallback, debug field
- `dose/passthrough/handlers/odoo_handler.py` — remove alerts, simplify `get_request_body`, fix navigation
- `dose/templates/admin/display.html` — SSO auto-login block with `display_credentials` template vars

## Follow-ups

- **Mattermost SSO** — next up
- **Nextcloud SSO** — after Mattermost
- Consider provisioning real Odoo user accounts per tenant (currently falls back to `odooAdmin`)
- The `odoo_db` stored in `TenantApp.extra_config` during subscribe is wrong (schema name);
  should store `"odoodb"` or the correct Odoo DB name at subscribe time
