# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-21 (Monday)
**Session:** Mailbox form — theme tokens, drop Jazzmin readonly box
**Branch:** main

## Done
- Removed Jazzmin “Published data” readonly field (white box ignored theme).
- Records only in `card` + `pre` styled with `--bs-body-*` and the same
  `data-bs-theme` / `data-ps-theme` dark hooks as the sidebar.

## Next
Rebuild → open a records row in light and dark THEMES; confirm readable.
Then **#2** async pull API.
