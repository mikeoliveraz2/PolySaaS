<!-- Shela 2026-09-24: read documentation/AGENT_NOTES_VENDOR_ASSIST.md before any vendor-assist edit. -->
**Vendor Assist agents:** read [AGENT_NOTES_VENDOR_ASSIST.md](AGENT_NOTES_VENDOR_ASSIST.md) before editing.

## Slice 6 topic (locked 2026-09-24)
- Publish to the **shared contacts topic** (`polysaas.capture.v1` / contacts family / existing enroll_contact_capture mailbox pattern).
- Do NOT use `slack.message.contact` (frozen customer-create consumer).
- Do NOT invent `polysaas.vendor.created` for this POC.
- Slice 6 still waits until Slice 4 (bind) and Slice 5 (save) are done. Do not implement Slice 6 yet.

## Slice 7 (not started) — live web / AI search
- Future: enable **live web / AI search** for the vendor shortlist. Today Slice 3 is curated **Demo directory** only.
- Out of scope until Michael says go **after Slices 4–6**. Do not invent web search now.
- LLM fail toast remains acceptable for Slice 3.

# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

## 2026-09-24 (Thursday) — Slice 7 recorded as future work (docs only)

- **Slice 7 (not started):** enable live web / AI search for vendor shortlist. Slice 3 remains curated Demo directory only.
- Out of scope until Michael says go after Slices 4–6. Do not invent web search now. LLM fail toast remains acceptable for Slice 3.
- Slice 6 still locked: shared contacts topic `polysaas.capture.v1`, not `slack.message.contact`, not `polysaas.vendor.created`.
- No Slice 4/5/6/7 code in this pack.

## 2026-09-24 (Thursday) — Type 4 POC Slice 4 (select/bind)

**Do not start Slice 5** (no Odoo RPC save) unless Michael says so. **Do not start Slice 6 or Slice 7.** Slice 7 (live web / AI search) waits until after 4–6.

- Click a Suggested vendors row: client fills Name, Email, Phone, Website, Main contact / Contact email from `data-*`. Same POST `/odoo/vendors/new` with `{step:"bind", bind_selection:true}` so `OdooVendorAssist` emits DoseMessage **"Vendor details loaded from selection"**. Missing name → **"Vendor selection bind failed"**; table stays. Save to Odoo still stub.
- **No new Instruction.** Existing POST REQ row. Optional seed: `python manage.py setup_odoo_vendor_assist_consumer --schema polysaas` (adds `bind_selection: true` on POST parameters).
- Canary: `Assist build table-visible-20260924+s4`. Tests: `dose.tests.test_odoo_vendor_lookup` — 29 passed. No odoo_handler vendor branch. Frozen `odoo_create_partner.py` untouched. `passthrough_embed.html` unchanged (`interesting()` already matches vendor).
- **Prod:** Deploy, hard refresh New Vendor Assist, click **SeaWrap**, form fills, toast **Vendor details loaded from selection**.

HEAD: `9bd2edef` (full: `9bd2edef4c2b49e40bd6c5f4073c0cbe3873f76f`).

## 2026-09-24 (Thursday) — SHELA: Type 4 POC New Vendor Assist Slices 1–3 (pull origin/main)

**Shela: start here for Slices 1–3 context.** Slice 4 is above. Do **not** start Slice 5, 6, or 7 unless Michael says so.

### What this is
Type 4 POC **New Vendor Assist**, Slices 1–3. Operator path: POLYSAASADMIN → Odoo passthrough → Purchase → Orders → Vendors → **New**. Branded Assist page (not Odoo’s form). GET serves the page + “Vendor page loaded”. **Find suppliers** POSTs JSON; Slice 2 captures criteria (“Criteria captured”). Slice 3 ranks a curated **Demo directory** (not live web). LLM rank **fails on prod** — **Shortlist search failed** toast is expected.

### Architecture (do not put vendor paths in the Odoo handler)
- Instruction **GET** `/odoo/vendors/new` → atomic `OdooVendorAssist` (`serve_page`)
- Instruction **POST** `/odoo/vendors/new` → same atomic (`capture_criteria` / shortlist)
- Generic instruction_page match only. **No hardcoded vendor path in the handler.**

### Prod
- Tenant **POLYSAASADMIN** / schema `polysaas`
- GET + POST Instructions exist
- Slice 2 verified (Criteria captured)

### Bug Shela should look at
After **5725f284**, prod showed **`Assist build bake-table-20260924`** but the **Suggested vendors** table was **not visible** under Find suppliers (likely `display:none` and/or passthrough_embed **`overflow:hidden` / clip** on `.polysaas-passthrough-scope`). This pack-up finishes a visibility WIP: table always in GET HTML under Find suppliers; body CSS `#ps-vendor-table-visible` tries to unclip the embed; version line **`Assist build table-visible-20260924`**. Tests: `dose.tests.test_odoo_vendor_lookup` — 27 passed.

### Key files
- `dose/services/odoo_vendor_lookup.py`
- `dose/templates/admin/odoo_vendor_lookup.html`
- `dose/passthrough/instruction_page.py`
- `dose/tests/test_odoo_vendor_lookup.py`
- `dose/management/commands/setup_odoo_vendor_assist_consumer.py`
- `dose/templates/admin/passthrough_embed.html` (`interesting()` already matches vendor/criteria/shortlist — **frozen, not edited this pack**)

### origin/main
- **origin/main:** `4555df1e` (full: `4555df1e58941aa8a3c7c924588e8d6836a9f02b`) — if a follow-up hash-line commit lands, pull again; this pack-up commit is `4555df1e`.

## 2026-09-24 (Thursday) — Bake Demo directory into GET HTML (no POST JSON required)

- **Problem:** 379df4d7 still looked like “no change” on prod (green bar refine skipped / Shortlist search failed, no vendor table). Rows depended on POST JSON + JS paint.
- **Fix:** GET `odoo_vendor_lookup.html` now includes a visible **Suggested vendors / Demo directory** table (SeaWrap, Mekong Film Co, ASEAN Office Supply, Graphite Point Stationery) immediately under **Find suppliers**. Version line under the title: **`Assist build bake-table-20260924`**. Find suppliers still POSTs and toasts; it does **not** clear baked rows (only replaces if POST actually returns vendors). Green bar: vendor/criteria/shortlist labels when action path contains `vendor`; **refine skipped** is not used for shortlist failed.
- Tests: `dose.tests.test_odoo_vendor_lookup` — 27 passed. No odoo_handler. No Slice 4.
- **Michael:** Deploy **this commit**. Hard refresh New Vendor Assist. He must see (1) **`Assist build bake-table-20260924`** under the title (2) the Suggested vendors table with named rows **before clicking Find suppliers**. If the version line is missing, Dokploy did not pick up the commit.

## 2026-09-24 (Thursday) — Demo rows even if JSON nested/empty; no stale toast parade

- **Root cause:** Find suppliers parsed `{ok, message}` (or `{json:{vendors}}`) and `data.vendors` was undefined, so `renderShortlist` painted nothing while Criteria captured still showed; green bar replayed every unread vendor/refine DoseMessage.
- **Fix:** JS `unwrapPayload(data.json || data)`, reads `vendors` or `suggested_vendors`, else hardcoded 4-row `DEMO_DIRECTORY`. Table always visible under Find suppliers (Name, Website/email, Main contact). Embed poll: `unread_messages`, **latest vendor toast only** (invoice still latest-only, no reverse stack).
- Tests: `dose.tests.test_odoo_vendor_lookup` — 26 passed.
- Michael: **Deploy this commit**, hard-refresh New Vendor Assist, **Find suppliers**. Expect 4+ named vendors. Old toasts should not parade. No Slice 4. No odoo_handler.

## 2026-09-24 (Thursday) — Vendor Assist shortlist: JSON POST + always-visible Demo table

- **Root cause:** `instruction_page._json_from_atomic_result` refused JSON whenever the atomic dict also had `html`, so Find suppliers POST could be **admin-wrapped HTML**; the page toasted Criteria captured locally, DoseMessage showed **Shortlist search failed**, and `#ps-shortlist-card` stayed `display:none` until a successful JSON parse.
- **Fix:** Generic JSON return for POST + Accept/json / X-Requested-With / `json_response` / nested `json` (no path hardcode). Atomic always returns serializable `{vendors: 3–6 demo rows}`. Template unhides `#ps-vendor-shortlist` (static 3-row Demo directory table under Find suppliers) on click; parse errors paint in red on the page; missing vendors shows **No vendors in response**.
- Tests: `dose.tests.test_odoo_vendor_lookup` — 25 passed.
- Michael: **Deploy this commit**, hard-refresh New Vendor Assist, click **Find suppliers**. Expect **Suggested vendors / Demo directory** table immediately under the button (SeaWrap, Mekong, ASEAN at minimum). Green bar may still say Shortlist search failed if the LLM is down — that is the toast, not an empty table. No new Instruction. No Slice 4.

## 2026-09-24 (Thursday) — Slice 3 shortlist render fix (Find suppliers empty table)

- **Root cause:** Find suppliers waited on `complete_chat` (30s, production LLM hang/403) *before* returning demo rows. Criteria DoseMessage fired first, so the page could show **Criteria captured** while the POST never finished the shortlist JSON. JS also required `Content-Type: json` and painted from `suggested_vendors`/`vendors` only after that wait — silent hidden table, no **Shortlist returned/failed**.
- **Fix:** Rank **Demo directory locally first** (always 3–6 rows, at least one `main_contact`). Optional LLM refine with **4s** timeout. JSON always `{ok, message, criteria, vendors, shortlist_status}`. JS parses JSON even if wrapped/HTML, always opens **Suggested vendors** / **Demo directory**. Status: Criteria captured **and** Shortlist returned or Shortlist search failed.
- Tests: `dose.tests.test_odoo_vendor_lookup` — 23 passed.
- Michael: **Deploy this commit**, hard-refresh New Vendor Assist, Find suppliers. Expect table immediately. No new Instruction. No Slice 4.

- **Root cause:** Find suppliers waited on `complete_chat` (30s, production LLM hang/403) *before* returning demo rows. Criteria DoseMessage fired first, so the page could show **Criteria captured** while the POST never finished the shortlist JSON. JS also required `Content-Type: json` and painted from `suggested_vendors`/`vendors` only after that wait — silent hidden table, no **Shortlist returned/failed**.
- **Fix:** Rank **Demo directory locally first** (always 3–6 rows, at least one `main_contact`). Optional LLM refine with **4s** timeout. JSON always `{ok, message, criteria, vendors, shortlist_status}`. JS parses JSON even if wrapped/HTML, always opens **Suggested vendors** / **Demo directory**. Status: Criteria captured **and** Shortlist returned or Shortlist search failed.
- Tests: `dose.tests.test_odoo_vendor_lookup` — 23 passed.
- Michael: **Deploy this commit**, hard-refresh New Vendor Assist, Find suppliers. Expect table immediately. No new Instruction. No Slice 4.

## 2026-09-24 (Thursday) — Type 4 POC Slice 3 (demo-directory shortlist)

- Slice 3 ready. Same **Find suppliers** POST on `/odoo/vendors/new` (same Instruction as Slice 2). After criteria capture, `OdooVendorAssist` ranks a curated **Demo directory** via RoutePlan + `complete_chat` (`LLM_ROUTER_STANDARD_MODEL`). If the LLM is down, a deterministic rank still returns 3–6 rows and toasts **Shortlist search failed**. LLM success toasts **Shortlist returned**.
- Page shows **Suggested vendors** / **Demo directory**. Rows are not bound (Slice 4). Save to Odoo still stub.
- Green bar `interesting()` now matches `shortlist` / `suggest`.
- **No new Instruction.** Same POST REQ row. Deploy only. Optional seed update: `python manage.py setup_odoo_vendor_assist_consumer --schema polysaas` (adds `suggest_vendors: true` on the existing POST parameters; not required for the atomic to run).
- Verify: POLYSAASADMIN → Purchase → Orders → Vendors → New → Find suppliers → page **Criteria captured** then **Shortlist returned** (or failed + still rows). Green bar follows.
- Next: Slice 4 select-and-bind. Do not start until owner says go.

## 2026-09-24 (Thursday) — Type 4 POC Slice 2 (criteria capture)

- Slice 2: operator clicks **Find suppliers** on New Vendor Assist. The page POSTs JSON to the same passthrough path. Instruction `POST REQ /odoo/vendors/new` → same atomic `OdooVendorAssist` records product line / region / price range, stores them in session, and emits DoseMessage **"Criteria captured"** (or a failure line on the green bar).
- GET page-load still emits **"Vendor page loaded"**. AI shortlist / bind / save / events are not in this slice.
- Green bar `interesting()` also matches `criteria` so the capture toast shows.
- After Dokploy deploy, seed the POST instruction (GET row already live):

```bash
python manage.py setup_odoo_vendor_assist_consumer --schema polysaas
```

  POST instruction fields if adding by hand: path `/odoo/vendors/new`, method `POST`, direction `REQ`, eventKey `odoo.vendor.new.assist.criteria`, executescript `OdooVendorAssist`, parameters `{"capture_criteria": true}`.
- Verify: POLYSAASADMIN → Odoo passthrough → Purchase → Orders → Vendors → New → **Find suppliers** (defaults filled) → green bar **Criteria captured**. Form values stay. Save still stub.
- Next: Slice 3 AI shortlist. Do not start until owner says go.

- Slice 2: operator clicks **Find suppliers** on New Vendor Assist. The page POSTs JSON to the same passthrough path. Instruction `POST REQ /odoo/vendors/new` → same atomic `OdooVendorAssist` records product line / region / price range, stores them in session, and emits DoseMessage **"Criteria captured"** (or a failure line on the green bar).
- GET page-load still emits **"Vendor page loaded"**. AI shortlist / bind / save / events are not in this slice.
- Green bar `interesting()` also matches `criteria` so the capture toast shows.
- After Dokploy deploy, seed the POST instruction (GET row already live):

```bash
python manage.py setup_odoo_vendor_assist_consumer --schema polysaas
```

  POST instruction fields if adding by hand: path `/odoo/vendors/new`, method `POST`, direction `REQ`, eventKey `odoo.vendor.new.assist.criteria`, executescript `OdooVendorAssist`, parameters `{"capture_criteria": true}`.
- Verify: POLYSAASADMIN → Odoo passthrough → Purchase → Orders → Vendors → New → **Find suppliers** (defaults filled) → green bar **Criteria captured**. Form values stay. Save still stub.
- Next: Slice 3 AI shortlist. Do not start until owner says go.

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
