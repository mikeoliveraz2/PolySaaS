# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-21 (Monday)
**Session:** Single Topics admin hub (scalable)
**Branch:** main

## Design (owner)
- **One Admin widget: Topics** — not one ModelAdmin per history type.
- Each topic row: **Browse queue** | **History** | Consume / Re-queue.
- 100 topics = 100 rows in one list. No sidebar explosion.

## Done
- Webhook mailboxes changelist redirects to Topics hub.
- Sidebar label: **Topics** (was Webhook mailboxes).
- Separate Inventory/SNMP/Maintenance history ModelAdmins removed from admin.
- Per-topic History view under the same hub.
- Migrations 0066/0067 still create the history tables (backend only).

## Hostinger
Deploy + migrate. Open Admin → **Topics**.

## Do not
- Re-add per-type history ModelAdmins to the sidebar.
- Call history “report.”
