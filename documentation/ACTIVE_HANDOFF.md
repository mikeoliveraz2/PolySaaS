# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-21 (Monday)
**Session:** Mailbox delete 500 — get_current_tenant path restore
**Branch:** main

## Root cause
`get_current_tenant()` looks up Tenant on `public` then **restores the previous
search_path** (often still `public`). That undid tenant SET before DELETE →
`webhook_mailbox` missing → 500 on bulk delete of 25 rows.

## Fix
- `resolve_request_tenant()` — public lookup without path undo footgun.
- WebhookMailboxAdmin: **skip LogEntry**; schema-qualified bulk DELETE.
- Ops fallback: `purge_webhook_mailbox --schema polysaas --all`

## Next
Rebuild django (**full image rebuild**), delete 25 again.
If still 500, run purge command and paste `docker logs` traceback.
