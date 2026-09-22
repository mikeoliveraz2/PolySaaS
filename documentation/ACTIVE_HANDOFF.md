# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-23 (Wednesday)  
**Session:** Type 3 — write the Note with the invoice page session  
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
- The Note write uses the Odoo `session_id` already stored for the invoice page (`TenantApp.extra_config`). The admin XML-RPC password is not required for this step. The cookie stays on the mailbox job only.
- VPS proof before this change: mailbox entry 205 ran `RefineOdooInvoiceDescription` and stopped at `Odoo authentication failed`. The bar stayed on “refining note…” because that failure text did not match the bar, and the older queue message was applied last.
- Unit tests: `dose.tests.test_refine_odoo_invoice_description` — 19 passed.

## Hostinger after deploy

```bash
git pull origin main
python manage.py setup_odoo_invoice_refine_consumer --schema polysaas
# mailbox consumer must be running
# collectstatic + restart so the bar script is ?v=20260923-t9
```

Demo: draft invoice with a messy Note → Confirm through passthrough → invoice posts → bar says the Note was refined → refresh shows the cleaned Note. Numbers stay put. A second Confirm does not loop.

## Next

1. Dokploy Deploy this commit (no re-seed). Hard-refresh. Reset 2Inv #13 to Draft, Confirm again. Bar should leave “refining note…” and the Note should be cleaned.
2. Type 2 analysis (when ready)
