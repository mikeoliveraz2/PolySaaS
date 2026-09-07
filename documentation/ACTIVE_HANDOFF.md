# PolySaaS Active Handoff

**Date:** 2026-09-07 (Monday)  
**Session:** Mattermost → Odoo Contact Creation BINGO  
**Branch:** main

## Summary

**BINGO achieved:** Mattermost → Odoo contact creation flow is now working end-to-end.

## Work Completed

### 1. Mattermost Outgoing Webhook Fixed
- **Root cause (Shela's insight):** Mattermost tokenizes on whitespace and matches first word only
- **Problem:** Trigger word `['New contact:']` (two tokens) could never match
- **Fix:** Changed to `['New']` (single token)
- **Result:** Webhook now fires, contacts appear in Odoo

### 2. Odoo Passthrough Display Fixed
- **Problem:** Waffle menu non-responsive, "Connection lost" errors
- **Cause:** HTTP 302 redirect in middleware converted POST→GET, breaking JSON-RPC
- **Fix:** Changed to HTTP 307 (preserves HTTP method) in `middleware.py`

### 3. Helper Scripts Created
- `scripts/list_mm_webhooks.py` — List MM outgoing webhooks
- `scripts/update_mm_webhook.py` — Update webhook config
- `scripts/create_mm_webhook.py` — Create new webhook
- `scripts/delete_old_mm_webhook.py` — Delete webhook by ID
- `scripts/enable_mm_internal.py` — Configure AllowedUntrustedInternalConnections

## Files Changed

| File | Change |
|------|--------|
| `dose/views/mattermost_events_webhook.py` | Added BINGO freeze banner |
| `dose/passthrough/middleware.py` | 302→307 fix (already frozen) |
| `scripts/update_mm_webhook.py` | Single-word trigger fix |
| `documentation/BINGO_MATTERMOST_ODOO_CONTACT_CREATION_2026-09-07.md` | New BINGO doc |

## Current State

- **Slack → Odoo:** Working (BINGO 2026-09-06)
- **Mattermost → Odoo:** Working (BINGO 2026-09-07) ✓
- **Odoo passthrough display:** Working (307 fix)
- **Mattermost passthrough:** Working (restored from BINGO)

## Mattermost Webhook Config

```
Trigger: ['New']  (single word!)
Callback: http://host.docker.internal:8000/hooks/mattermost/events/
Content-Type: application/json
```

## Next Actions

1. Consider adding feedback message to Mattermost channel when contact is created
2. Test edge cases (duplicate contacts, invalid emails, etc.)

## Commit Status

Ready for BINGO commit and push.
