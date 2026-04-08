# BINGO — Mattermost Phase 1 display shell + full client shim

**Date:** 2026-04-08  
**Status:** Tested and confirmed by user — "bingo" (Town Square + channels + history in Phase 1 shell; spinner resolved)

## What was delivered

1. **`dose/templates/admin/display.html`**  
   Odoo-only body scoping (`MutationObserver`, `appendChild` interception, “Moving Odoo node…”) is gated behind **`{% if display_enable_odoo_body_scope %}`** so Mattermost/Nextcloud/Vue/React are not broken by Odoo-specific DOM hijack.

2. **`OdooPassthroughHandler`**  
   Passes **`display_enable_odoo_body_scope: True`** when rendering `admin/display.html` (unchanged Odoo behavior).

3. **`MattermostPassthroughHandler`**  
   - **`try_root_display_shell_response`**: prepends the **full** client shim (not only token + `__webpack_public_path__`).  
   - Shim includes **`toProxy`**, **`fetch`**, **`XMLHttpRequest.open`**, **`WebSocket`**, prototype/`setAttribute` patching, plus **MMAUTHTOKEN** seeding — same behavior for display shell and **`process_html_response`** / normal HTML proxy path.  
   - **`base_origin`** for the shim comes from **`endpoint.endpoint_url`**.  
   - Passes **`display_enable_odoo_body_scope: False`**.

4. **Clarity (no behavior change where already safe)**  
   **`NextcloudPassthroughHandler`** and **`passthrough_display_shell_view`** pass **`display_enable_odoo_body_scope: False`** explicitly.

5. **Backups**  
   `.bak` copies alongside edited sources per project rule.

## Verified (user session)

- Full Mattermost UI inside Phase 1 orchestration shell: workspace, channels, **Town Square**, message history.  
- Console: **`[PolySaaS Mattermost] Full shim loaded`** and MMAUTHTOKEN injection.  
- Network: API traffic under **`/pt/admin/mattermost/api/v4/...`** (not bare `/api/v4/...` on the admin host).  
- Non-blocking: internal “Something went wrong while loading the component” banner, plugin noise (e.g. GitHub 501, Calls 403, mattermost-ai user lookup), WebSocket flakiness — noted; **core chat UI usable**.

## Files touched (this bingo)

| Path | Role |
|------|------|
| `dose/templates/admin/display.html` | Odoo body-scope gate |
| `dose/passthrough/handlers/odoo_handler.py` | `display_enable_odoo_body_scope: True` |
| `dose/passthrough/handlers/mattermost_handler.py` | Display shell + full shim, shared with HTML proxy |
| `dose/passthrough/handlers/nextcloud_handler.py` | Explicit `False` for Odoo scope flag |
| `dose/admin_views.py` | Test shell: explicit `False` |
| `*.bak` | Backups paired with edits |

## Follow-ups (not part of this bingo)

- Nextcloud: port **8888**, endpoint URL, handler parity + stream logger (next todo).  
- Mattermost: true WebSocket bridging vs plugin errors if we want zero console noise and no bottom banner.

## Git

- [x] `git pull origin main`  
- [x] Commit with this bingo doc + listed sources  
- [x] `git push origin main`
