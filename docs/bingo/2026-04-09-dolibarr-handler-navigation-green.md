# BINGO — Dolibarr Handler: Internal Navigation + Asset Rewriting

**Date:** 2026-04-09
**Certified by:** Michael (manual test)
**Commit covers:** `dose/passthrough/handlers/dolibarr_handler.py`, `dose/passthrough/handlers/registry.py`

---

## What Was Achieved

Dolibarr 19.0.2 renders correctly and navigates inside the PolySaaS display shell at
`/pt/admin/dolibarr/`. Sidebar, setup sections, SMS settings, and module pages all load
with correct layout and internal navigation.

---

## Changes

### `dose/passthrough/handlers/dolibarr_handler.py` (new file)

- `process_html_response`: rewrites root-relative and upstream-absolute URLs in
  Dolibarr HTML responses so assets and navigation stay inside `/pt/admin/dolibarr/`
- Covers all Dolibarr asset roots: `/theme/`, `/core/`, `/includes/`, `/public/`,
  `/custom/` and module paths (`/societe/`, `/facture/`, `/compta/`, etc.)
- Script-body-safe: stashes `<script>` bodies before rewriting (same pattern as
  Nextcloud handler) to prevent JSON/logic corruption
- `<style>` blocks get `url()` rewriting only — no bulk string replacement
- No display shell needed — Dolibarr is server-rendered PHP, not a Vue/React SPA

### `dose/passthrough/handlers/registry.py`

- Added `dolibarr` trigger → `DolibarrPassthroughHandler` entry

---

## Architecture Note

Dolibarr required no `try_root_display_shell_response` (no SPA boot issue). The generic
forwarder + `process_html_response` hook is sufficient for PHP-rendered apps.
This same pattern applies to any future PHP-based bundled app.

---

## Test Performed

1. Navigated to `/pt/admin/dolibarr/` via PolySaaS sidebar
2. Logged in: admin / admin
3. Setup page rendered with correct layout
4. Sidebar navigation worked: Setup → SMS, My Dashboard, Admin Tools, Users & Groups
5. Server log showed `[DOLI-HANDLER] HTML rewrite complete` on every page

**Status: BINGO — internal navigation confirmed working.**
