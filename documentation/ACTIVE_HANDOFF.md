# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-19 (Saturday)
**Session:** BINGO — Mattermost Browse search_path (FROZEN)
**Branch:** main

## Done
- Hostinger Founders tenant schema `polysaas`; Odoo + Mattermost provisioned.
- Browse 404 root cause: `PassthroughAuthMiddleware` clobbered `search_path` to `public`.
- Fix `a0bc2367`; tenant-data-in-public rules reinforced `feb5a3d2`.
- **BINGO FROZEN (commit ``b8b827cd``):** `documentation/BINGO_MM_BROWSE_SEARCHPATH_TENANT_SCHEMA_2026-09-19.md`
  — `dose/middleware/passthrough_auth.py` must not be edited without owner permission.
- GOLD ZIP: `D:\BINGO ZIPS\BINGO_MM_BROWSE_SEARCHPATH_2026-09-19.zip`

## Next
1. Optional: persist `MATTERMOST_ADMIN_TOKEN` in Dokploy; rotate temp MM admin password.
2. Do **not** touch frozen passthrough_auth without Michael/Shela approval.
