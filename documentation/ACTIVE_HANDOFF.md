# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday)
**Session:** Fix mailbox Tenant shadow lookup
**Branch:** main

## Done
- Root cause of seed/enroll failure: `Tenant.objects.get` under
  `search_path=polysaas,public` hit a **shadow empty** `polysaas.dose_tenant`.
- `create_from_envelope(..., tenant=)` — use caller’s Tenant; never look up
  Tenant while on tenant-only path without forcing public.

## Next (Hostinger)
```bash
# Rebuild django first, then:
python manage.py diagnose_webhook_mailbox --schema polysaas --seed
```
Refresh Webhook mailboxes — expect SEED row. Then re-hit Inventory.
