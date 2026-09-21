# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-21 (Monday)
**Session:** Mailbox admin delete 500 — real fix
**Branch:** main

## Cause (revised)
Prior fix restored search_path after log, but Django `log_deletions`
still **re-queried** `webhook_mailbox` while `search_path=public` → 500
*during logging*, before delete.

## Fix
- Materialize pk/repr on tenant schema first.
- Write `LogEntry` only with `search_path=public`.
- Delete via schema-qualified SQL (`"{schema}".webhook_mailbox`).
- Ops: `python manage.py purge_webhook_mailbox --schema polysaas --all`

## Next (Hostinger)
**Rebuild** django (must pick up `dose/admin_base.py`), then delete in Admin.
If still blocked:
```bash
python manage.py purge_webhook_mailbox --schema polysaas --dry-run
python manage.py purge_webhook_mailbox --schema polysaas --all
```
Then resume **#2** async pull API.
