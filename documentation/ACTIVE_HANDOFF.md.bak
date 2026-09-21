# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-21 (Monday) — continuing  
**Session:** Cross-app Capture contacts (Odoo + Mattermost) → Captured Topics  
**Branch:** main  
**Prior BINGO:** `documentation/BINGO_CAPTURED_TOPICS_CONSUME_HISTORY_2026-09-21.md` (`7a6913b4`)

## In progress / just built

Cross-app **Capture contacts** (GET-style list → mailbox → Consume → `ContactHistory`):

- `dose/services/contact_capture.py` — normalize + enroll `RES.<app>.contacts.<actor>`
- `dose/services/odoo_capture_contacts.py` — paginated Odoo `res.partner` customers
- `dose/services/mattermost_list_contacts.py` — paginated `GET /api/v4/users`
- `dose/endpoint_actions/contact_capture_publish.py` — Control Panel publishers
- Bookmarks: Odoo + Mattermost **Capture contacts**
- `ContactHistory` + migration `0068_contact_history`
- `FAMILY_CONTACTS` in `topic_consume.py` (owner-approved freeze edit)

## How to use

1. `python manage.py migrate` (all schemas)
2. Odoo / Mattermost Control Panel → **Capture contacts**
3. Admin → **Captured Topics** → Browse → **Consume to History**
4. Topic History shows `source_app`, name, email, …

## Next

1. Migrate + smoke-test Capture contacts on `polysaas` / `olient`
2. Type 2 SNMP video (deferred from morning plan)
3. Later apps: Slack / HubSpot capture_contacts using same enroll helper

## Frozen note

Captured Topics consume/history files were edited with owner approval for contacts family.
Do not reopen unrelated frozen files without permission.
