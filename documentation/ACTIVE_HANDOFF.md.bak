# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday)
**Session:** Fix empty Webhook mailbox on Odoo SPA navigate
**Branch:** main

## Done
- Root cause: Odoo green-bar uses `/dose/api/orchestration-navigate/` which only
  fired **REQ** and never had an upstream body — `CaptureGetResponse` skipped
  before mailbox enroll.
- Fix: navigate API fires **REQ + RES**; CaptureGetResponse enrolls mailbox on
  navigate-without-body (capture_mode=navigate).

## Next (Hostinger)
1. Rebuild django (`ad089dd2` + this navigate fix).
2. Leave Inventory → return (reset action gate) → check Webhook mailboxes.
