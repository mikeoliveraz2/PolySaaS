# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday) — EOD
**Session:** Inventory mailbox capture verified (Hooray)
**Branch:** main
**Latest:** `90015500` (+ this handoff/doc commit)

## Done today
- Schema-safe WebhookMailbox (no Tenant FK; `db_table=webhook_mailbox`).
- **CapturePostResponse** captures Odoo `web_search_read` **result.records**
  (Inventory products) into mailbox.
- Admin list shows `N record(s)`; change form **Published inventory records**
  banner shows the product table.
- Hostinger verified: product.template rows with 10 inventory products visible.

Doc: `documentation/SESSION_2026-09-20_INVENTORY_MAILBOX_CAPTURE.md`

## Tomorrow — #2
**Async pull API** for mailbox subscribers (by topic / mailbox id, until TTL).
Capture + Admin browse is complete; pull is next.

## Do not
- Treat `/odoo/action-384` navigate rows as inventory data.
- Put tenant-owned mailbox rows in `public`.
