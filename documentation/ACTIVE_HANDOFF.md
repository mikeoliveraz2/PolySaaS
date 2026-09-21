# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-21 (Monday)
**Session:** Topic browser + Consume → report tables
**Branch:** main

## Done
- **Topic model (aligned):** temp store = typed topic; Consume drains to report tables;
  Admin browses end tables.
- Models: `InventoryProductReport`, `SnmpTelemetryReport`, `MaintenanceEquipmentReport`
  (`dose/models/topic_report.py`, migration `0066_topic_report_tables`).
- Service: `dose/services/topic_consume.py` (list topics + consume).
- Admin: Topic browser at `/admin/dose/webhookmailbox/topics/` with **Consume** button;
  report changelists registered.
- Captures + SNMP enroll as **pending** (not processed). Background trigger consumer
  skips capture/snmp so Consume owns the drain.
- SNMP Odoo feed moved to Consume (optional after SNMP topic drain).
- Stripe webhook route restored earlier (`/dose/webhook/stripe/`).

## Next (Hostinger)
1. Deploy + `python manage.py migrate` (all schemas) for 0066.
2. Open Topic browser → Consume inventory product topic first.
3. Browse **Inventory products (report)**.
4. New captures/feeds land pending; Consume again for SNMP.

## Note
Older mailbox rows already marked `processed` will not Consume until re-queued
(or new inventory sniff / new SNMP posts).

## Do not
- Put tenant-owned report rows in `public`.
- Run Odoo writes on webhook accept for SNMP (Consume path only).
