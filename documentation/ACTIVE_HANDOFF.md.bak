# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday)
**Session:** Empty mailbox — diagnose + enroll-before-publish
**Branch:** main

## Done
- CaptureGetResponse: **mailbox enroll before MQ publish** (write-free).
- `diagnose_webhook_mailbox --schema polysaas [--seed]` for Hostinger.

## Next (Hostinger) — run in Django container
```bash
python manage.py diagnose_webhook_mailbox --schema polysaas --seed
```
Then refresh Webhook mailboxes. If seed row appears, admin/schema are fine and
Inventory Instruction path is still not calling enroll (Rebuild / Instruction).
If seed row does **not** appear, schema/table problem.
