# Mattermost Passthrough — EOD Handoff (2026-06-05)

**Status**: WIP — Zero-cache success state reached, but SPA still does not fully boot.

## What Is Working (Proven This Session)

- Aggressive clean-boot shim now executes on every fresh `plugin_booted=1` load.
- 26-character plugin token is correctly injected into:
  - `localStorage` (`MMAUTHTOKEN` + `mmauthtoken`)
  - Cookies (`MMAUTHTOKEN`, `mmauthtoken`)
  - IndexedDB (`persist:storage`)
- Native Mattermost login UI is actively blocked (history-replaceState + DOM observers).
- Plugin auth check returns `valid: true` for the provisioned user.
- Error query `?type=team_not_found` on the root path is now intercepted and forces a clean `/?plugin_booted=1&force=1` redirect.
- Critical indentation bug fixed: `_build_token_reseed_html` is now a proper top-level class method (was accidentally nested inside `_wrap_login_bridge`).

## What Is Still Broken

- Mattermost SPA requests critical static assets directly against the upstream origin:
  - `manifest.js` → 404
  - Multiple chunk files (`*.js`, `*.css`) → 404
- Because the manifest and core bundles never load, the authenticated main app never initializes.
- Result: browser remains stuck on the native Mattermost login form or the "Loading • • •" spinner.

## Root Cause

The current client-side shim rewrites `fetch`/`XHR` but does **not** rewrite the `<script src>` and asset loader URLs that the Mattermost bundle injects at runtime. Server-side HTML rewriting (`_rewrite_mattermost_assets`) was never implemented.

## Files Modified in This Session (WIP worktree)

- `dose/passthrough/handlers/mattermost_handler.py`
  - Added `handle_passthrough` (currently dead code — not wired into routing).
  - Added `?type=...` error-query guard in `try_root_display_shell_response`.
  - Fixed indentation of `_build_token_reseed_html` (critical bug fix).
- Multiple `.bak*` files created during the session (should be committed as historical record).

## Next Step (Office Machine)

Implement server-side asset URL rewriting in `process_html_response` (and the reseed path) so that all `/static/...`, `/plugins/...`, and `/api/...` references in the HTML are rewritten to go through `/pt/admin/{host}/...`.

Once that is in place, the SPA should receive its bundles through the passthrough, the injected token will be honored, and Town Square should render.

## Commands to Resume

```powershell
cd F:\PolySaaS-worktrees\wip
.\runwt          # or the equivalent from repo root
```

Hard refresh the PolySaaS admin, then click Mattermost.

---

**Owner**: Michael  
**Date**: 2026-06-05 (EOD)  
**Branch**: wip (F:\PolySaaS-worktrees\wip)