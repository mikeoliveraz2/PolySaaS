# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday)
**Session:** Odoo inventory sample seed command
**Branch:** main

## Done
- Prior: Mattermost Browse search_path BINGO frozen (`b8b827cd`).
- New: `python manage.py seed_odoo_inventory` — 10 storable SKUs (`PS-INV-01`..`10`)
  with on-hand qty via stock.quant (Odoo 18 `is_storable`).

## Next (Hostinger)
1. Dokploy Rebuild django if needed so the new command is in the image.
2. `python manage.py seed_odoo_inventory --schema polysaas`
3. Confirm Odoo Inventory shows `PS-INV-*` on-hand.
4. Resume week orchestration cases (GET extract, correlation, mid-stream refine, AI UI).
