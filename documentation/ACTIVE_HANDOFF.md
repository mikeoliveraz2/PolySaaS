# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-23 (Wednesday)  
**Session:** Type 3 simplified — one atomic, observe and write back  
**Branch:** main  

## Done

- Type 3 is one atomic: `RefineOdooInvoiceDescription`.
  - Live invoice Confirm POST (`/web/dataset/call_button`, account.move + action_post) is forwarded to Odoo unchanged, then the atomic queues a mailbox job and returns.
  - Mailbox replay reads `account.move.narration` (the invoice Note), AI-cleans it, writes it back. Idempotent. Fail-soft.
  - `EnqueueOdooInvoiceRefine` is only an alias onto that same atomic.
- Seed: `python manage.py setup_odoo_invoice_refine_consumer --schema polysaas`
  - One passthrough Instruction: POST RES contains `/web/dataset/call_button` → `RefineOdooInvoiceDescription`
  - One mailbox transport row on `/events/odoo/invoice/refine` (same atomic)
  - Removes old `EnqueueOdooInvoiceRefine` instructions
- Green bar no longer paints “ready — refine on Post” / standing-by. After Confirm it shows the DoseMessage: refining, refined, no change, or AI unavailable.
- Unit tests: `dose.tests.test_refine_odoo_invoice_description` — 14 passed. Live Confirm click on the VPS was not run in this session.

## Hostinger after deploy

```bash
git pull origin main
python manage.py setup_odoo_invoice_refine_consumer --schema polysaas
# mailbox consumer must be running
# collectstatic + restart so the bar script is ?v=20260923-t9
```

Demo: draft invoice with a messy Note → Confirm through passthrough → invoice posts → bar says the Note was refined → refresh shows the cleaned Note. Numbers stay put. A second Confirm does not loop.

## Next

1. Deploy, run the seed, hard-refresh, Confirm one dirty draft on the VPS
2. Type 2 analysis (when ready)
