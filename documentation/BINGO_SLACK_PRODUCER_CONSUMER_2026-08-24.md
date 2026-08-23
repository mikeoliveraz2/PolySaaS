# BINGO — Slack home + producer/consumer pairing — 2026-08-24

<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Slack producer/consumer home — 2026-08-24 -->

## Certified
- Slack Browse is a real top-level Slack UI (no iframe).
- Slack app home shows:
  - Bookmarks: Channel home, New contact, New sale (rail hidden when empty elsewhere).
  - Producers (allowlist only): slack.webhook.contact, slack.webhook.sale — Paired.
  - Consumers: OdooCreatePartner / OdooCreateQuotation, fed by those producers, Run intact.
- New contact and new sale already flow through mailboxes (plumbing earlier today).
- Odoo Browse remains usable on OLIENTR.

## Explicitly not this bingo
- Green-bar orch copy / instruction-match messaging
- Slack-shaped popups for contact/sale
- Full Slack webhook surface
- HubSpot

## Sequence still locked
Native HAR → passthrough → pair producers to consumers → popups/orch UX.

## Handoff
Tenant: OLIENTR. Apps: Odoo + Slack. Machine of record must commit this file and push before switch.

**Commit**: `28b07da0` on `cursor/polysniffer-slack-native-capture`  
**GOLD ZIP**: `D:\BINGO ZIPS\BINGO_slack_producer_consumer_2026-08-24.zip`

## Frozen source files
| File | Role |
|------|------|
| `dose/endpoint_producers.py` | Allowlist + pair helpers |
| `dose/views/endpoint_home.py` | Home + producer-pair API |
| `dose/urls.py` | `producer-pair` route |
| `dose/templates/dose/endpoint_home.html` | Producers / Consumers UI |
| `dose/static/admin/css/endpoint_home.css` | Home styles |
| `dose/static/admin/js/endpoint_home.js` | Pair dialog + Run |
| `dose/tests/test_endpoint_home.py` | Architecture tests |
| `documentation/ACTIVE_HANDOFF.md` | Handoff |
| `documentation/BINGO_SLACK_PRODUCER_CONSUMER_2026-08-24.md` | This cert |

## Validation
- `python manage.py test dose.tests.test_endpoint_home` — 12 OK
- Browser OLIENTR: Slack home + live top-level Slack Browse
- GOLD ZIP: `D:\BINGO ZIPS\BINGO_slack_producer_consumer_2026-08-24.zip`
