# BINGO — Nextcloud Phase 1 Shell Green

**Date:** 2026-04-10
**Status:** Tested and confirmed by user — "perfect"
**Commit covers:** `dose/templates/admin/display.html`, this bingo note

---

## What Was Achieved

Nextcloud now logs in and runs correctly inside the PolySaaS Phase 1 display shell at
`/pt/admin/nextcloud/`, with the main content area using the full available width and the
sidebar/header no longer clipping the shell controls.

---

## Code Changes

### `dose/templates/admin/display.html`

- Added a shell-specific body class: `polysaas-display-shell-page`
- Dropped the right-side Recent Actions column for display-shell pages so passthrough apps use
  the full available content width
- Removed extra Jazzmin container padding/margins inside the shell content track
- Preserved fixed-header clearance for the shell grid and increased the shell-specific header
  offset to keep the orchestration bar and sidebar header fully visible
- Raised the sidebar/header stacking order so the collapse control remains clickable
- Removed the negative orchestration-bar margin that was contributing to edge and clip issues

---

## Verification

1. Direct Nextcloud login was re-tested against `http://localhost:8888/`
2. Proxied Nextcloud login was re-tested against `/pt/admin/nextcloud/`
3. Authenticated OCS user checks returned HTTP `200` for both direct and proxied flows
4. User confirmed the final shell result as: `next cloud is perfect`

---

## Operational Note

The live Nextcloud instance had drifted from the original compose seed credentials. During
verification, the upstream `admin` password had to be reset inside the running container using
`occ user:resetpassword` because the persisted instance no longer accepted the original seeded
value. That password reset was an environment operation only and is **not** part of this commit.

---

## Scope Boundaries

- Committed: shell layout and header/sidebar interaction fixes in `display.html`
- Not committed: live container password reset, runtime-only validation steps

**Status: BINGO — Nextcloud login + Phase 1 shell layout confirmed green.**