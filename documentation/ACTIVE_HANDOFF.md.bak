# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-22 (Tuesday)  
**Session:** Odoo Capture contacts setup instructions  
**Branch:** main  

## Doc

**Setup guide:** [documentation/SETUP_ODOO_CAPTURE_CONTACTS.md](SETUP_ODOO_CAPTURE_CONTACTS.md)

## Hostinger polysaas — quick path

1. `python manage.py migrate`
2. Odoo PassThroughEndpoint: slug `odoo`, URL `http://odoo:8069` (already verified on container)
3. Open `/pt/admin/odoo/` (not host-based `localhost:8069`)
4. Control Panel → **Capture contacts**
5. Captured Topics → Consume to History

## Notes

- Menu/Browse may still link `/pt/admin/<host>/` via `get_menu_url()` — use slug URL `/pt/admin/odoo/`
- Capture needs Odoo RPC password (env `ODOO_XMLRPC_ADMIN_PASSWORD` or TenantApp.extra_config)
- Image must include Capture contacts code (`cfb7fa1e+`) for the button

## Next

1. Smoke-test Capture contacts on polysaas
2. Same setup for Slack/HubSpot endpoints when image has `61f026d9`
3. Type 2 SNMP video
