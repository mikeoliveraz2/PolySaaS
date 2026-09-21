# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-21 (Monday)
**Session:** Type 2 SNMP → Odoo Maintenance Phase A+B implemented
**Branch:** main

## Done
- **SnmpToOdooMaintenance** atomic (`dose/services/snmp_to_odoo_maintenance.py`):
  enroll `WebhookMailbox` first, then upsert `maintenance.equipment` by MAC→`serial_no`,
  create `maintenance.request` on `status=down` or `temperature_c >= 60`.
- Wired `snmp` into `generic_inbound_webhook` registry + source map.
- Seed: `python manage.py seed_snmp_odoo_maintenance [polysaas|olient]`
- Feed: `python scripts/snmp_week_feed.py --week 1|2 --tenant polysaas`
  (Week 1/2 = data scenarios run back-to-back — no calendar wait.)
- Plan doc updated to “in progress / implement”.

## Next (Hostinger)
1. Confirm Maintenance app on shared Odoo.
2. `python manage.py seed_snmp_odoo_maintenance polysaas`
3. `python scripts/snmp_week_feed.py --week 1 --tenant polysaas`
4. `python scripts/snmp_week_feed.py --week 2 --tenant polysaas`
5. Verify Admin Webhook mailboxes + Odoo Equipment / Requests (split-screen film).

## Defer
- Async mailbox pull API (Admin browse enough for demo).
- Real PolySysMon / SNMP agent.

## Do not
- Put SNMP/mailbox/Odoo orchestration rows in `public`.
- Wait calendar weeks between feeds — only change the data (`--week 1` then `--week 2`).
