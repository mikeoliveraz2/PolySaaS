# BINGO: Mattermost → Odoo Contact Creation

**Date:** 2026-09-07  
**Status:** VERIFIED WORKING  
**Commit:** (pending)

## What Was Verified

1. **Mattermost outgoing webhook fires** when user types `New contact: Name, email, Company` in any public channel
2. **Webhook hits PolySaaS endpoint** at `/hooks/mattermost/events/`
3. **Contact is parsed and published** to the same `slack.message.contact` topic used by Slack
4. **Odoo consumer creates the contact** in Odoo CRM (same instruction as Slack flow)
5. **Both Bob Marley (earlier) and Test Person appeared in Odoo** after fix

## The Critical Fix

**Problem:** Mattermost outgoing webhooks weren't triggering — zero log entries, silent failure.

**Root Cause (identified by Shela):** Mattermost tokenizes messages on whitespace and matches the **first word only** against trigger words. The configured trigger `['New contact:']` (two tokens with a space) could never match because the first word of `"New contact: Name..."` is just `"New"`.

**Solution:** Changed trigger word from `['New contact:']` to `['New']` (single token).

## Architecture

```
Mattermost (user types message)
    ↓ outgoing webhook (trigger: "New")
/hooks/mattermost/events/
    ↓ parse "New contact: Name, email, Company"
    ↓ verify mm_team_id + mm_webhook_token
publish_slack_contact_event()
    ↓ RabbitMQ topic: slack.message.contact
Odoo consumer (existing instruction)
    ↓ creates res.partner in Odoo
```

## Files Involved

| File | Purpose |
|------|---------|
| `dose/views/mattermost_events_webhook.py` | Webhook endpoint — FROZEN |
| `dose/webhook_events.py` | `publish_slack_contact_event()` — shared with Slack |
| `dose/passthrough/middleware.py` | 302→307 fix for POST preservation — FROZEN |
| `scripts/update_mm_webhook.py` | Helper to update MM webhook config |

## Mattermost Webhook Configuration

```
ID: to8h4hjgabyzxqrnmdw39gom5h
Team: polysaas-team
Channel: (all channels)
Trigger words: ['New']
Trigger when: 0 (exact match on first word)
Callback: http://host.docker.internal:8000/hooks/mattermost/events/
Content-Type: application/json
```

## TenantApp Configuration Required

In `TenantApp` for Mattermost (`app_name='mattermost'`), `extra_config` must include:
- `mm_team_id`: The Mattermost team ID (for tenant lookup)
- `mm_webhook_token`: The outgoing webhook token (for verification)
- `mm_url`: Mattermost server URL
- `mm_token`: Admin API token (for webhook management)

## Also Fixed This Session

**Odoo display broken (waffle menu non-responsive):**
- Cause: HTTP 302 redirect in `middleware.py` converted POST→GET, breaking Odoo's JSON-RPC calls
- Fix: Changed to HTTP 307 (preserves HTTP method)

## Test Commands

```powershell
# List webhooks
python scripts/list_mm_webhooks.py

# Update webhook trigger
python scripts/update_mm_webhook.py
```

## Acknowledgment

Thanks to **Shela** for identifying the single-word trigger requirement — that was the key insight that unblocked this after hours of debugging.
