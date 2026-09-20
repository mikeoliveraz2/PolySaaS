# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday)
**Session:** Mailbox admin records table
**Branch:** main

## Done
- WebhookMailboxAdmin **Published records** renders `records[]` as an HTML
  table (id, code, name, qty, …), not raw JSON.
- Digs nested `data` / `result.records` for older captures.

## Next (Hostinger)
Rebuild django, hard-refresh Admin → open a capture row with product data.
Expect a table of inventory records under Published data.
