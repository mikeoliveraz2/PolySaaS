# BINGO — Odoo Handler Cleanup Green

**Date:** 2026-04-10
**Status:** Tested and confirmed by user — Odoo, Nextcloud, Dolibarr, and Mattermost all green
**Commit covers:** `dose/templates/admin/includes/custom_sidebar.html`, this bingo note

---

## What Was Achieved

Odoo passthrough was cleaned up so the handler is again the single authoritative Odoo path.
The remaining admin-layer hardcoded Odoo views were removed, handler auth was restored to
tenant/app configuration, and the silent localhost fallback was removed.

After bringing the Odoo demo stack up, `/pt/admin/odoo/` rendered successfully inside the
PolySaaS Phase 1 shell and tested green alongside Nextcloud, Dolibarr, and Mattermost.

---

## Runtime State

At verification time, Odoo passthrough was green with the handler-driven cleanup in place:

- no legacy `admin/odoo-view/` path in use
- Odoo auth resolved from configured tenant/app data
- no hidden localhost fallback masking upstream errors

This bingo commit itself records the final verified state and the shared admin header-offset fix
approved immediately before recording.

---

## Code Changes In This Commit

### `dose/templates/admin/includes/custom_sidebar.html`

- Increased the shared admin header offset from `57px` to `64px`
- Updated the admin wrapper height to use the shared `--pss-header-h` variable

This fixes the slight top clipping on the base admin dashboard so the sidebar and content area
sit fully below the fixed navbar.

### `docs/bingo/2026-04-10-odoo-handler-cleanup-green.md`

- Records the Odoo green verification state and the final dashboard offset polish before recording

---

## Verification

1. Verified active Odoo upstream accepted TCP connections on `localhost:8069`
2. Verified `GET /web/login` returned `200`
3. Verified JSON-RPC auth to `/web/session/authenticate` returned `200`, `uid=2`, and a real `session_id`
4. Verified `GET /pt/admin/odoo/` through PolySaaS returned `200` with the orchestration shell and no upstream error banner
5. User confirmed Odoo, Nextcloud, Dolibarr, and Mattermost are all green
6. User approved the final shared admin top-offset tweak as `perfect`

---

## Operational Note

Starting Odoo from `docker-compose.demo-sync.yml` was an environment/runtime step only and is
not part of this commit. This commit captures the final verified state plus the last admin-layout
polish approved immediately before recording.

---

## Outcome

- The big four passthrough endpoints are verified green
- The base admin dashboard no longer clips the sidebar/content under the fixed navbar
- The UI is in recording-ready shape for the video

**Status: BINGO — Odoo cleanup + verification green.**