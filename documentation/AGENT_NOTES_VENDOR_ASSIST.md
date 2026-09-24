<!-- AGENT CONTEXT — Michael 2026-09-24 — read before any vendor-assist edit -->

## Type 4 Vendor Assist — locked spine
- Path: GET+POST `/odoo/vendors/new` → Instruction → atomic `OdooVendorAssist`
- NOT hardcoded in the Odoo passthrough handler. If you add an if-vendor branch in the handler, REJECT and undo.
- Odoo remains SoR. No second vendor table.
- Frozen customer-create service: do not modify (`odoo_create_partner.py`).

## HEAD / pack
- Update after commit. Key files: `dose/services/odoo_vendor_lookup.py`, `dose/templates/admin/odoo_vendor_lookup.html`, `dose/passthrough/instruction_page.py`, `dose/tests/test_odoo_vendor_lookup.py`, `dose/management/commands/setup_odoo_vendor_assist_consumer.py`

## Slice status
- Slices 1–4. Slice 4: click Suggested vendors row → bind Name/Email/Phone/Website (+ main contact) from `data-*` plus POST `{step:"bind", bind_selection:true}` on the same `/odoo/vendors/new` Instruction. DoseMessage **"Vendor details loaded from selection"**. Fail-soft on bind failure (do not clear table).
- **Do not start Slice 5** (no Odoo RPC save) unless Michael explicitly says.
- Slice 3: LLM shortlist **fail toast is acceptable** when search fails; do not invent live web search.
- Curated/demo directory only for shortlist data unless Michael expands scope.

## Toasts (do not collapse into one)
Per-step DoseMessage on success and failure: page loaded, criteria captured, shortlist returned/failed, vendor details loaded from selection / bind failed.

## Out of scope
Live web vendor search, multi-app fan-out, new hosts, pixel Odoo clone, Slice 5–6 until ordered.

## Prod verify Slice 4
Deploy, hard refresh New Vendor Assist, click **SeaWrap**, form fills, toast **Vendor details loaded from selection**. Save to Odoo stays stub.
