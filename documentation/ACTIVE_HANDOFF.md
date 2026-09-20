# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday)
**Session:** Restore WebhookMailbox db_table
**Branch:** main

## Done
- Dropped tenant FK (0065) — migrate OK on public/olient/polysaas.
- Seed failed: ORM used default `dose_webhookmailbox`; real table is
  `webhook_mailbox` (set in 0061). Restored `Meta.db_table`.

## Next (Hostinger)
Rebuild django (no migrate needed), then:
```bash
python manage.py diagnose_webhook_mailbox --schema polysaas --seed
```
Expect SEED OK. Then Inventory → mailbox.
