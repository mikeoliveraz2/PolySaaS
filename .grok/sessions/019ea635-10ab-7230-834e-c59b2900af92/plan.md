# Implementation Plan: Improve "+ Insert Orchestration Instruction" Button on Passthrough Embed Pages

## Context
The "+ Insert Orchestration Instruction" button appears on the green/dark "● POLYSAAS ORCHESTRATION ACTIVE — PASSTHROUGH EMBED" bar in passthrough embed pages (Odoo, Mattermost, Nextcloud, Dolibarr, etc.).

This bar + button is delivered uniformly because `dose/passthrough/forwarding.py:_wrap_in_admin_template` (called for qualifying HTML responses during passthrough forwarding) renders `dose/templates/admin/passthrough_embed.html` around upstream content. Handlers can influence wrapping via `should_wrap_in_admin_template` / `passthrough_embed_template_context`, but the bar/JS/button HTML lives in the shared template.

Currently the button's click handler (in the template's inline script) only does:
```js
alert('Instruction will be created for action path:\n' + path + '\n\n(Feature coming soon)');
```
The bar already computes and displays the live "Action Path" (the inner path after `/pt/admin/<trigger>/`, e.g. `/web`, `/channels/town-square`, `/odoo/...` etc.) using `getOdooPath()` / `#pss-action-path`.

The user wants the button to open the **standard admin "Add Instruction" form** (the full `InstructionAdmin` experience with all fields, the atomic service dropdown from the registry, fieldsets, etc.), pre-filled with the current Action Path as `requestpath`, for the current tenant. After save, standard admin success + the existing bar polling will surface the new instruction.

Constraints (piccolo passo): minimal clean changes, maximal reuse of existing instruction creation/admin/form/tenant logic, no new views/forms/models, works for all wrapped passthrough services.

## Recommended Approach
1. Extend `InstructionAdmin` (which already inherits `TenantAwareModelAdmin`) with the standard Django hook `get_changeform_initial_data(request)` to read `?requestpath=...` from the query string and supply sensible defaults (`match_type`, `direction`). This is the idiomatic, zero-UI-change way to prefill admin add forms and is already used in the same file (AtomicServiceAdmin).

2. Replace only the button's click listener in `passthrough_embed.html` (the single place that currently renders the exact "+ Insert..." button + the Action Path display). Use the path the bar is already showing, build the admin add URL with the query param, and `window.open(..., '_blank')` so the live passthrough SPA remains undisturbed. The bar's existing 2s `updateBar` + `/dose/api/orchestration-navigate/` polling provides the "refresh" behavior naturally.

3. Tenant is handled automatically: passthrough requests have a tenant on the request/session; `TenantAwareModelAdmin.get_queryset`/`save_model` (in `admin_base.py`) does the `SET search_path` and the `Instruction` (a `TenantAwareModel`) is saved under the correct tenant schema. No query param or extra code for tenant is required. The `create_instruction` helper in `orchestration.py` is intentionally left untouched (it is a different, simpler dashboard flow).

This reuses:
- The full admin form + `InstructionForm` (executescript choices, validation, inlines, fieldsets).
- All tenant scoping machinery.
- The bar's existing path extraction and polling.
- The forwarding layer that already puts this template in front of every service.

No changes to models, URLs, handlers (beyond what they already support), or the orchestration dashboard creator.

## Critical Files to Modify
- `dose/admin.py` — Add `get_changeform_initial_data` inside `class InstructionAdmin(TenantAwareModelAdmin):`.
- `dose/templates/admin/passthrough_embed.html` — Replace only the `btn.addEventListener('click', ...)` block (the alert) with the new navigation logic. Do not touch bar HTML/CSS, path computation functions, polling, history hooks, or the "FROZEN" header comments.

Other files are read-only for understanding or will benefit automatically:
- `dose/passthrough/forwarding.py` (the `_wrap_in_admin_template` at lines ~238-287 that renders the template for all services; also calls optional `passthrough_embed_template_context`).
- `dose/passthrough/handlers/handler_base.py` (defines the `passthrough_embed_template_context` and `should_wrap...` hooks; no code change needed).
- `dose/models/instruction.py` (the `Instruction` model with `requestpath`, `match_type`, `direction`, `TenantAwareModel` base).
- `dose/admin_base.py` (the `TenantAwareModelAdmin` that guarantees tenant schema for queries/saves).
- `dose/utils.py` (`get_current_tenant(request)` — already called by the admin base and inside InstructionAdmin for the executescript dropdown).
- `dose/views/orchestration.py` (`create_instruction` and `orchestration_dashboard` — reference only; not used for the "standard form").

## Existing Code / Utilities to Reuse (with paths)
- `InstructionAdmin` + `InstructionForm` (full form with registry-powered executescript select, fieldsets, `add_view`/`save_model` overrides): `dose/admin.py:291` (class) and surrounding (formfield_for_dbfield, get_form, save_model, inlines added later at 768).
- `TenantAwareModelAdmin.get_queryset` / `save_model` + schema switching: `dose/admin_base.py:16-92` (especially `save_model` lines 34-57 which calls `get_current_tenant`).
- `get_current_tenant`: `dose/utils.py:5` (used by admin base and by InstructionAdmin for tenant-aware service choices).
- Bar + Action Path display + `getOdooPath()` / `pathEl.textContent` + history/poll logic: `dose/templates/admin/passthrough_embed.html:232-396` (the entire script IIFE; we only edit the final 7 lines of the click handler).
- Wrapping that puts the template in front of every passthrough: `dose/passthrough/forwarding.py:238` (`_wrap_in_admin_template`), called from forwarder (around line 1000 in practice) and used by Odoo/Mattermost/etc. handlers via the registry.
- Model fields: `dose/models/instruction.py:26-39` (`requestpath`, `match_type=PATH` default, `direction=REQ` default, etc.).
- Admin add URL pattern: standard Django `/admin/dose/instruction/add/` (registered at `dose/admin.py:811`).
- Existing prefill pattern: `dose/admin.py:46` (`AtomicServiceAdmin.get_changeform_initial_data`).

## Design Trade-offs Considered
- Using the dashboard's `create_instruction` view (orchestration.py:57) instead of the admin form: rejected — user explicitly wants "the standard 'Add Instruction' form (same as in the admin interface)".
- Opening a custom modal duplicating the form fields: rejected — violates "reuse ... as much as possible" and "minimal".
- Always navigating in same tab vs `_blank`: chose `_blank` (keeps complex SPA state in Odoo/Mattermost alive; user can switch tabs). Easy to change to `location.href` later.
- Pre-filling more fields or using `contains` vs `path` default: chose minimal (`path` + `REQ`) matching the model's defaults and the bar's purpose; user can adjust in the real form.
- Injecting button JS into every handler shim: unnecessary for this step — the forwarding wrap already gives the template (and thus the button) to all services. Handlers that opt out of wrap are out of scope.
- Adding success toast back on the embed page or `?next=` return link: out of scope for piccolo passo (admin success message + existing bar poll satisfy the requirement).

## Verification (End-to-End Test Steps)
1. Start the app with a tenant that has at least one passthrough endpoint (Odoo, Mattermost, etc.) configured and reachable.
2. As a tenant user, navigate into a passthrough embed (e.g. `/pt/admin/<trigger>/web?...` or a Mattermost channel path). Confirm the dark bar appears with "Action Path: ..." and the green "+ Insert Orchestration Instruction" button.
3. Note the exact Action Path string shown.
4. Click the button. A new browser tab should open directly to `/admin/dose/instruction/add/?requestpath=<encoded-path>&match_type=path&direction=REQ`.
5. Verify the standard admin "Add Instruction" form loads (all fieldsets, the executescript `<select>` populated from the registry via `InstructionForm`, etc.).
6. Confirm the `requestpath` input is pre-filled with the exact path from the bar (without the `/pt/admin/<trigger>` prefix).
7. Fill the remaining required/interesting fields (choose an Atomic Service, description, optionally save_callbackdata, etc.), submit.
8. Observe the normal Django admin success message on the resulting page (changelist or detail).
9. Return to (or reload) the original passthrough embed tab. The bar should continue functioning; subsequent navigation or the 2s poll should be able to produce matches against the newly created instruction for that tenant (visible in "matched X" status or via the orchestration dashboard / Instruction admin list filtered to the tenant).
10. Confirm the created Instruction record lives in the tenant's schema (not public) by inspecting via admin or DB under the tenant schema.
11. Repeat quickly for a second service (e.g. Mattermost channel path) to prove cross-service behavior.
12. Negative: clicking the button with no tenant context should still reach the admin (which will handle or show tenant warnings per existing TenantAware behavior).

Manual testing is sufficient; no new automated tests are added in this minimal change.

## Implementation Notes / Order
- First implement the admin prefill (easy to test in isolation by visiting the add URL with a query param).
- Then the tiny JS change in the template.
- Keep the edit inside the existing `(function(){ ... })();` IIFE; preserve every other line of the bar logic.
- After the two changes, the feature is complete. No other files need modification for the stated requirements.

This plan is the smallest possible delta that fully satisfies the request while obeying reuse and "piccolo passo".
