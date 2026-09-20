# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday)
**Session:** Mailbox admin shows published payload (demo)
**Branch:** main

## Done
- WebhookMailboxAdmin: **Published data** section + list **Payload** column
  (reads `envelope.payload`, falls back to `result`).
- Capture enroll `result` now stores full `data` / meta for browse.
- Seed includes payload in `result`.

## Next (Hostinger)
Rebuild django. Open existing rows — Published data should show payload.
Re-seed or hit Inventory for a fresh row with richer `result`.
