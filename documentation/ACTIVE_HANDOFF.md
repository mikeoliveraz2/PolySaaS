# Active Handoff — 2026-09-07 (BINGO, Laptop)

This file is the canonical startup and end-of-day handoff. Every agent must read it before editing or answering.

## Session Summary
**BINGO:** Mattermost passthrough restored for PolySaaSOline Town Square (2026-09-07). Slack → Odoo left intact.

## What Was Completed

- Restored `mattermost_handler.py` + `middleware.py` from Mattermost BINGO `8100b79a`
- Fixed PolySaaSOline TenantApp token (was expired `ebojaniy…` on the wrong tenant)
- Pointed landing team at existing `polysaas-team` (not missing `polysaas-dev-team`)
- Michael verified live: Town Square + onboarding modal under `/pt/admin/mattermost/`
- Certification: `documentation/BINGO_MATTERMOST_PASSTHROUGH_RESTORED_2026-09-07.md`

## Frozen — do not edit without owner

```
THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
```

- `dose/passthrough/handlers/mattermost_handler.py`
- `dose/passthrough/middleware.py`
- Slack → Odoo BINGO `e9f5f20f` (unchanged)

## Next (≈20 min) — Mattermost webhook onto Slack topic

Do **not** touch the frozen handler/middleware.

1. Keep `/hooks/mattermost/events/` as a thin adapter
2. Parse `New contact: Name, email, Company`
3. Call existing `publish_slack_contact_event()` — same mailbox / `slack.message.contact` / OdooCreatePartner
4. Configure Mattermost Outgoing Webhook + `mm_webhook_token` / `mm_team_id` on PolySaaSOline
5. Post the contact line in Town Square and confirm the Odoo partner

Slack files stay frozen. No second producer.

## Current Branch & Commit

- **Branch:** cursor/polysniffer-slack-native-capture
- **Mattermost BINGO today:** see `documentation/BINGO_MATTERMOST_PASSTHROUGH_RESTORED_2026-09-07.md`
- **Slack BINGO:** e9f5f20f

## Blockers
None for passthrough. Webhook E2E not done yet.

---
*Updated 2026-09-07 after live Town Square verification (PolySaaSOline / michael.oliver).*
