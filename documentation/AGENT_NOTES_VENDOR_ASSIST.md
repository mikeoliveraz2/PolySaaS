<!-- AGENT CONTEXT — Michael 2026-09-25 — read before any vendor-assist edit -->

## Slice 6 topic (locked 2026-09-24)
- Publish to the **shared contacts topic** (`polysaas.capture.v1` / contacts family / existing enroll_contact_capture mailbox pattern).
- Do NOT use `slack.message.contact` (frozen customer-create consumer).
- Do NOT invent `polysaas.vendor.created` for this POC.
- Slice 6 is **not started**. Do not implement Slice 6 yet.

## Slice 7 (not started) — live web / AI search
- Future: enable **live web / AI search** for the vendor shortlist. Today Slice 3 is curated **Demo directory** only.
- Out of scope until Michael says go **after Slices 4–6**. Do not invent web search now.
- LLM fail toast remains acceptable for Slice 3.

## Type 4 Vendor Assist — locked spine
- Path: GET+POST `/odoo/vendors/new` → Instruction → atomic `OdooVendorAssist`
- NOT hardcoded in the Odoo passthrough handler. If you add an if-vendor branch in the handler, REJECT and undo.
- Odoo remains SoR. No second vendor table.
- Frozen customer-create service: do not modify (`odoo_create_partner.py`).

## HEAD / pack
- Key files: `dose/services/odoo_vendor_lookup.py`, `dose/templates/admin/odoo_vendor_lookup.html`, `dose/passthrough/instruction_page.py`, `dose/tests/test_odoo_vendor_lookup.py`, `dose/management/commands/setup_odoo_vendor_assist_consumer.py`

## Slice status
- Slices 1–5. Slice 5: **Save to Odoo** creates company partner + optional linked contact. Same POST Instruction, `{step:"save"}`. DoseMessages **Vendor created** / **Contact linked** or fail-soft contact / company. Open Odoo’s form targets created `res.partner` id. **No event publish.**
- **Do not start Slice 6** until Michael says go (shared contacts topic only — see locked topic above).
- **Do not start Slice 7** (live web / AI search) until Michael says go after 4–6.
- Slice 3: LLM shortlist **fail toast is acceptable** when search fails; do not invent live web search.
- Curated/demo directory only for shortlist data unless Michael expands scope (that expansion is Slice 7).

## Toasts (do not collapse into one)
Per-step DoseMessage on success and failure: page loaded, criteria captured, shortlist returned/failed, vendor details loaded from selection / bind failed, vendor created, contact linked / contact link failed — vendor still created, vendor create failed.

## Out of scope
Live web / AI vendor search (**Slice 7**, until ordered after 4–6), multi-app fan-out, new hosts, pixel Odoo clone, Slice 6 until ordered.

## Prod verify Slice 5
Deploy, hard refresh New Vendor Assist, click **SeaWrap**, **Save to Odoo**. Expect **Vendor created** then **Contact linked**. Open Odoo’s form shows the created vendor (not a blank form).
