<!-- AGENT CONTEXT — Michael 2026-09-25 — read before any vendor-assist edit -->

## Type 4 Vendor Assist — locked spine
- Path: GET+POST `/odoo/vendors/new` → Instruction → atomic `OdooVendorAssist`
- NOT hardcoded in the Odoo passthrough handler. If you add an if-vendor branch in the handler, REJECT and undo.
- Odoo remains SoR. No second vendor table.
- Frozen customer-create (`odoo_create_partner.py`) and frozen `odoo_handler.py`: do not modify.

## Slice status
- Slices 1–6 done.
- **Slice 6:** publish only after successful company save, via `publish_saved_vendor_capture` → `enroll_contact_capture`. Kind `polysaas.capture.v1`. Key `odoo.capture_contacts` / path `odoo/contacts`. Not `slack.message.contact`. Not `polysaas.vendor.created`. No consumer Instruction.
- **Slice 7 not started** (live web / AI search). Demo directory only until Michael says go.
- **Lina Tan visual check still on Michael.**

## Canary
`Assist build table-visible-20260924+s4+s5+s6`

## Toasts (do not collapse into one)
Per-step DoseMessage: page loaded, criteria, shortlist, bind, vendor created, contact linked/fail, event published / event publish failed.

## Out of scope
Live web vendor search, multi-app fan-out consumers, Mattermost/Slack/HubSpot event wiring, new hosts, pixel Odoo clone.
