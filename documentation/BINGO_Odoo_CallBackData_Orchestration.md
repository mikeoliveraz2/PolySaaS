# BINGO — Odoo CallBackData Orchestration Working

**Date:** 2026-05-31  
**Status:** ✅ COMPLETE — Tested and verified locally  
**Tenant:** `polysaast122` (pOLYsAAs tEST 122)  
**Branch:** main  

---

## Summary

Odoo passthrough navigation now triggers dynamic orchestration from the client-side green bar.
When a user opens Odoo Accounting (`/odoo/accounting`), the system matches Instruction id=17,
runs the `HelloWorld` atomic service, and persists audit rows to **Call Back Data** with
`matchingEventKey=odoo_invoicing_viewed`.

Verified in admin: **Admin → Call Back Data** shows rows with description
*"User viewed Invoicing in Odoo"* and JSON payload including path, eventKey, and instruction_id.

---

## What Works

1. **Green orchestration bar** on the Odoo display shell tracks path, menu id, and action.
2. **`POST /dose/api/orchestration-navigate/`** fires on Odoo SPA navigation (history hooks).
3. **Instruction matching** — rule `/odoo/accounting/116` matches navigation to `/odoo/accounting`
   (Odoo 18 path normalization in `orchestration_hook.py`).
4. **Atomic service execution** — `HelloWorld` runs when instruction matches.
5. **CallBackData persistence** — rows saved when `save_callbackdata=True` on the instruction.
6. **Structured orchestration logging** — `[ORCH]` trace lines via `orchestration_log.py`.

---

## Root Cause Fixed (green bar "API error")

The orchestration navigate API returned **403 CSRF** because:

- `getCsrfToken()` read a stale hidden `csrfmiddlewaretoken` from the admin shell instead of
  the live `csrftoken` cookie (header and cookie values did not match).
- `orchestration_navigate_api` imported `csrf_exempt` but never applied the decorator.

**Fix:** `@csrf_exempt` on the login-protected API (same pattern as `odoo_sso_api.py`), and
cookie-first CSRF token lookup in `display.html` / `passthrough_embed.html`.

---

## Test Instruction (tenant `polysaast122`)

| Field | Value |
|-------|-------|
| id | 17 |
| requestpath | `/odoo/accounting/116` |
| requestmethod | GET |
| match_type | path |
| executescript | HelloWorld |
| save_callbackdata | True |
| eventKey | odoo_invoicing_viewed |

---

## Files Changed

### Orchestration core
- `dose/orchestration_navigate_api.py` — client navigation trigger API; `@csrf_exempt`
- `dose/passthrough/orchestration_hook.py` — instruction match, atomic run, CallBackData save
- `dose/passthrough/orchestration_log.py` — structured `[ORCH]` logging (new)
- `dose/urls.py` — wire `api/orchestration-navigate/`

### Display / embed UI
- `dose/templates/admin/display.html` — green bar, history hooks, orchestration notify
- `dose/templates/admin/passthrough_embed.html` — same orchestration bar pattern

### Odoo passthrough
- `dose/passthrough/handlers/odoo_handler.py` — path rewrite, display shell, shim
- `dose/passthrough/incoming_path_rewrite.py` — bare Odoo path → `/pt/admin/...`
- `dose/passthrough/middleware.py` — hook integration

### Admin / models
- `dose/models/instruction.py` — instruction fields for orchestration
- `dose/admin.py` — instruction admin, CallBackData admin
- `dose/services/atomic_services_registry.py` — atomic service registry
- `dose/views/atomic_service_names.py` — atomic service name API
- `dose/static/admin/js/instruction_atomic_service.js` — instruction form helper (new)
- `templates/atomic_instruction_form.html` — orchestration form tweaks

---

## How to Reproduce

1. Log in as tenant user on `polysaast122`.
2. Open Odoo via display shell (e.g. `/odoo/accounting` or passthrough embed).
3. Green bar should show **matched 1, saved 1** (not "API error").
4. Open **Admin → Call Back Data** — new row with `odoo_invoicing_viewed`.

---

## Follow-ups

- Wire additional Odoo menu paths as Instructions (e.g. Sales, CRM).
- Replace `HelloWorld` with production services (`OdooInvoiceNotifierService`, etc.) per use case.
- Consider deduplicating CallBackData on repeated navigation to the same path in one session.

---

**BINGO — Odoo CallBackData orchestration is live.**
