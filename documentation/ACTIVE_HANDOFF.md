# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

## 2026-09-24 (Thursday) — Type 4 POC Slice 1 pushed

- Slice 1 New Vendor Assist code pushed: Instruction `GET /odoo/vendors/new` → atomic `OdooVendorAssist` → branded page + "Vendor page loaded" toast.
- Slice 1 works on prod (dynamic orchestration). Next is PolySaaS logo on the branded page, then Slice 2 (not started).
- Next: Dokploy rebuild. Then add the instruction on prod (tenant `polysaas`): path `/odoo/vendors/new`, `GET`, `REQ`, eventKey `odoo.vendor.new.assist`, executescript `OdooVendorAssist`, parameters `{"serve_page": true}`. Then verify on screen via Purchase → Orders → Vendors → New.
- Slices 2–6 are not started.

**Date:** 2026-09-23 (Wednesday)  
**Session:** BINGO — Odoo invoice Note refine on 2Inv #13  
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

## Done this session

- Refine failures now include the error text in the DoseMessage (Odoo session, AI HTTP status, model name). The invoice Note is not copied onto the bar.
- The green bar keeps that sentence next to `orch: refine skipped` instead of flashing it for 12 seconds.
- Unit tests: `dose.tests.test_refine_odoo_invoice_description` — passed locally.

## BINGO

Verified on polysaas.online, invoice **2Inv #13**. The green bar showed `orch: refined` and `Invoice 2Inv #13 description refined`. The note lines are now "Now we will see if this gets refined." and "Adding second note". `Just another note.` and the product line were left as they were. Doc: `documentation/BINGO_ODOO_INVOICE_NOTE_REFINE_2026-09-23.md`.

## Next

1. Dokploy deploy the invoice-field contrast fix (rules are in the embed page itself, and the shim paints the inputs). Hard-refresh the draft invoice after the deploy finishes. The previous deploy did not change the black fields.
2. Type 2 analysis (when ready)
