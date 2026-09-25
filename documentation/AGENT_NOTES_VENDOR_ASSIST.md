<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Type 4 New Vendor Assist — 2026-09-25 -->
<!-- AGENT CONTEXT — Michael 2026-09-25 — read before any vendor-assist edit -->

## Type 4 Vendor Assist — locked spine
- Path: GET+POST `/odoo/vendors/new` → Instruction → atomic `OdooVendorAssist`
- NOT hardcoded in the Odoo passthrough handler. If you add an if-vendor branch in the handler, REJECT and undo.
- Odoo remains SoR. No second vendor table.
- Frozen customer-create service: do not modify.
- No Odoo URL refactor (`odoo:8069`) until Type 4 video is done.

## Slice status
- Slices 1–7 done on the same GET/POST Instruction. **No new Instruction.**
- Slice 7: Find suppliers uses existing LLM router (`RoutePlan` + `complete_chat` / `LLM_ROUTER_STANDARD_MODEL`). There is **no web-search tool** on that router. Rows from the LLM are labeled **AI suggested**. Fail-soft (8s timeout) paints curated **Demo directory** rows and toasts **Shortlist search failed**. Success toasts **Shortlist returned** (Criteria captured stays its own toast). SeaWrap/Mekong/etc. stay as fallback/padding.
- Slice 6 (two topics): vendor company → `enroll_vendor_capture` / **Vendors**. Contact → `enroll_contact_capture` / **Contacts**. No consumer that writes other apps.
- Canary: `Assist build table-visible-20260924+s4+s5+s6+s7`

## Toasts (do not collapse into one)
Per-step DoseMessage on success and failure: page loaded, criteria captured, shortlist returned/failed, bind, save, publish.

## Out of scope
Paid web search APIs / new hosts (needs Michael approval), multi-app fan-out consumer, URL redesign, handler vendor special-case.
