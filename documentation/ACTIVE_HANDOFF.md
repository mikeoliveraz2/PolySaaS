# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday)
**Session:** Fix mailbox records visibility (truncate + admin table)
**Branch:** main

## Done
- `_truncate` no longer strips `records[]` (was turning large Odoo lists into
  `_preview` only — admin then showed no records).
- Admin **Published records** uses a plain-text table in `<pre>` (Jazzmin-safe).
- Diagnose `--seed` writes sample inventory `records[]`; `--dump` shows shape.
- Capture Instructions also match `search_read`.

## Next (Hostinger)
```bash
# Rebuild, then:
python manage.py setup_odoo_inventory_capture --schema polysaas
python manage.py diagnose_webhook_mailbox --schema polysaas --seed
python manage.py diagnose_webhook_mailbox --schema polysaas --dump
```
Open the newest SEED row in Admin — expect a table with PS-INV-01..03.
Then reload Odoo Inventory Products via passthrough for a live capture.
