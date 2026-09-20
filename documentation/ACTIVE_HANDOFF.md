# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday)
**Session:** Drop WebhookMailbox.tenant FK (schema isolation)
**Branch:** main

## Done
- Seed failed: FK `webhook_mailbox_tenant_id → dose_tenant_slug` against
  empty shadow `polysaas.dose_tenant` (Tenant lives in `public` only).
- Migration `0065_webhookmailbox_drop_tenant_fk`: removed `tenant` FK;
  `event_id` unique within schema; consumer index is status+expires_at.
- `create_from_envelope` no longer stores Tenant; schema from envelope only.
- Call sites that filtered `tenant=` on mailbox rows updated.

## Next (Hostinger)
```bash
# Rebuild django (pulls migration), then:
python manage.py migrate
python manage.py diagnose_webhook_mailbox --schema polysaas --seed
```
Expect SEED row in Webhook mailboxes. Then Inventory → mailbox enroll.
