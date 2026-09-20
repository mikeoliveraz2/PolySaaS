# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday)
**Session:** Mailbox/topic pattern — capture enroll + dead letter
**Branch:** main

## Done
- CaptureGet/Post **write-free** enroll `WebhookMailbox` with MQ **topic**
  (`source=passthrough`, status=processed, useful TTL default **7 days**).
- Past useful life → **dead_letter** (inspectable); purge after **14 days**
  via `python manage.py maintain_webhook_mailboxes`.
- Migration `0064_webhookmailbox_topic_dead_letter` adds `topic` column.
- Admin list shows topic + dead_letter status.

## Next (Hostinger)
1. Rebuild django + `python manage.py migrate` (all schemas).
2. Re-hit Odoo Inventory GET Instruction → **Webhook mailboxes** should show
   `source=passthrough`, topic `RES.…`, status processed.
3. Optional cron: `maintain_webhook_mailboxes` periodically.
