# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday)
**Session:** CapturePostResponse — inventory records from web_search_read
**Branch:** main

## Done
- Inventory products live in the Odoo **POST** `web_search_read` **response**
  (`result.records`) before SPA render — not in navigate/CallBackData.
- Added **`CapturePostResponse`** (RES + POST) — extracts that dict, normalizes
  `records[]` into mailbox payload.
- Admin shows record count + records in Published data.
- Command: `setup_odoo_inventory_capture --schema polysaas`

## Next (Hostinger)
```bash
# Rebuild django, then:
python manage.py setup_odoo_inventory_capture --schema polysaas
```
Open Odoo Inventory (Products) via passthrough → refresh Webhook mailboxes.
Expect a row with payload `records: [ … products … ]`.
