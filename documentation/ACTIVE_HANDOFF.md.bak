# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-22 (Tuesday)  
**Session:** Capture contacts on Slack + HubSpot Control Panels  
**Branch:** main  
**Prior BINGO:** Captured Topics Consume — `7a6913b4`

## Completed

**Capture contacts** now on all four apps:

| App | Action | Topic |
|-----|--------|--------|
| Odoo | `odoo.capture_contacts` | `RES.odoo.contacts.*` |
| Mattermost | `mattermost.capture_contacts` | `RES.mattermost.contacts.*` |
| HubSpot | `hubspot.capture_contacts` | `RES.hubspot.contacts.*` |
| Slack | `slack.capture_contacts` | `RES.slack.contacts.*` |

Shared path: list → mailbox enroll → Consume → `ContactHistory` (`source_app`).

## Slack note

Needs bot token on `TenantApp.extra_config.bot_token` (xoxb-…) with `users:read` (+ `users:read.email` for emails). Falls back to `SLACK_BOT_TOKEN` setting/env.

## Next

1. `migrate` if `0068_contact_history` not applied yet
2. Smoke-test Capture contacts on each Control Panel
3. Type 2 SNMP video
