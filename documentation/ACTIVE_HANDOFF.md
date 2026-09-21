# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-22 (Tuesday)  
**Session:** Odoo Control Panel New contact + dynamic orch  
**Branch:** main  

## Done

- Odoo CP bookmark **New contact** (`odoo.contact` popup) → mailbox  
  path `/events/odoo/control-panel/contact` → **OdooCreatePartner**
- Seed: `python manage.py setup_odoo_cp_contact_consumer --schema polysaas`
- Shared contact form wired via `action_urls.odoo_contact` + `data-contact-path`
- Setup doc updated: [SETUP_ODOO_CAPTURE_CONTACTS.md](SETUP_ODOO_CAPTURE_CONTACTS.md)

## Hostinger after deploy

```bash
python manage.py setup_odoo_cp_contact_consumer --schema polysaas
# ensure mailbox consumer is running
```

Then: Odoo Control Panel → **New contact** → Save → watch orch bar.

## Next

1. Redeploy image with this commit
2. Seed consumer + smoke-test New contact
3. Type 2 SNMP video
