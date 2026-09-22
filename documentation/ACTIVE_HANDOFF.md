# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-22 (Tuesday)  
**Session:** Type 3 — Refine Odoo invoice narration mid-stream  
**Branch:** main  

## Done

- Type 3 refine pipeline:
  - `EnqueueOdooInvoiceRefine` — passthrough RES match on `/web/dataset/call_button` (filters `account.move` + `action_post`) → mailbox
  - `RefineOdooInvoiceDescription` — AI clean → write `account.move.narration` (idempotent, fail-soft)
  - Seed: `python manage.py setup_odoo_invoice_refine_consumer --schema polysaas`
- Field locked: **narration** only (v1)
- Type 2 SNMP analysis deferred (Michael thinking)

## Hostinger after deploy

```bash
python manage.py setup_odoo_invoice_refine_consumer --schema polysaas
# mailbox consumer must be running
```

Demo: create invoice with messy/rude narration → Post via Odoo passthrough → green bar → refresh → cleaned narration + CallBackData before/after.

If enqueue does not fire, confirm live Post path on orch bar and adjust enqueue Instruction `requestpath`.

## Next

1. Redeploy + seed + smoke Type 3 demo
2. Type 2 analysis (when ready)
3. Optional: commit mailbox “Published contact records” title fix if not already on Hostinger
