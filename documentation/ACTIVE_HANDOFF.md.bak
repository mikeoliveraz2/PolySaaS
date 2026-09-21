# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-21 (Monday)
**Session:** Topics + Consume → history (not “report”)
**Branch:** main

## Done
- Topic list at `/admin/dose/webhookmailbox/topics/` — click a topic to browse envelopes.
- Topic detail: peek envelopes, **Consume → history**, **Re-queue processed → pending**.
- History tables (renamed from report): Inventory / SNMP / Maintenance.
  Models: `InventoryProductHistory`, `SnmpTelemetryHistory`, `MaintenanceEquipmentHistory`.
  Migrations: `0066` then `0067_topic_history_rename`.

## How to use
1. Topics page = temporary queues (list).
2. Click a topic = browse that queue.
3. Consume = move pending into history.
4. History changelists = permanent analysis store.

## Hostinger
```text
python manage.py migrate
```
Then open Topics → click `RES.product.template…` → Re-queue if needed → Consume → Inventory history.

## Do not
- Call history tables “reports.”
- Put tenant-owned history in `public`.
