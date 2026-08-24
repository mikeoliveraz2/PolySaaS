# PolySaaS Active Handoff

<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Slack producer/consumer home — 2026-08-24 -->

This file is the canonical startup and end-of-day handoff for the repo.
Every agent — Copilot, Cursor, and Windsurf — must read it before work.

## Status

- Date/session: 2026-08-24 EOD — Slack New Contact Odoo look + Save → Odoo
- Branch: `cursor/polysniffer-slack-native-capture`
- Cert: `documentation/BINGO_SLACK_PRODUCER_CONSUMER_2026-08-24.md` (`28b07da0`)
- Agent sync check: passed
- Tenant of record: **OLIENTR** (Odoo + Slack). This machine also used **polysaasonline**.
- GOLD ZIP: `D:\BINGO ZIPS\BINGO_slack_producer_consumer_2026-08-24.zip`

## Work completed (this EOD)

Slack **New contact** now looks like Native Odoo Contacts / New. Save queues the mailbox, closes the sheet, and `OdooCreatePartner` writes the partner. Live smoke: mailbox `#19` created **Slack Display 141623** on `localhost:8086`.

- Odoo-styled contact sheet (purple bar, New/search chrome, avatar, Individual/Company, underline fields).
- Save no longer looks dead: Saving…, close-on-queue, green bar above the overlay, success copy **Shown in Odoo Contacts — {name}**.
- Contact payload forwards `street`, `city`, `zip`, `is_company`.
- Green-bar instruction-match copy was already on this branch (`9716b7a8`).

Frozen BINGO source files were not edited.

## Files changed

- `dose/templates/polysniffer/slack_wireframe.html` (+ `.bak`)
- `dose/static/admin/js/slack_wireframe.js` (+ `.bak`)
- `dose/endpoint_actions/slack.py` (+ `.bak`)
- `dose/views/slack_wireframe_webhook.py` (+ `.bak`)
- `dose/tests/test_slack_wireframe_webhooks.py` (+ `.bak`)
- `dose/static/admin/css/orchestration_bar.css` (+ `.bak`)
- `dose/templates/dose/includes/orchestration_bar.html` (+ `.bak`)
- `documentation/ACTIVE_HANDOFF.md` (+ `.bak`)

## Validation

- `python scripts/check_agent_sync.py` — passed
- `python manage.py test dose.tests.test_slack_wireframe_webhooks` — 6 OK
- Live signed-in client: Slack Save → mailbox processed → Odoo partner created

## Next (condo)

**Duplicate the New Contact look-and-feel and Save UX onto New sale.** Sale stays Slack-dark today. Mirror the Odoo quotation/form chrome, keep `partner_name` + `order_reference` required, same close-on-queue + bar SUCCESS path to `OdooCreateQuotation`. Do not reopen producer/consumer pairing or Browse.

After pull: restart Waitress + hard-refresh Slack home (`slack_wireframe.js?v=20260824-6`).

## Sequence still locked

Native HAR → passthrough → pair producers to consumers → popups/orch UX.

## Blockers / risks

- Coordinated migrate still blocked at legacy `dose.0028_mlprompt`. Do not fake
  without an audited plan.

## Commit exclusions

**Exclude:** `documentation/Capital Raise Project/**`, `polysniffer-auth.json`,
`polysniffer_evidence/`, `tmp/_probe_*`, `tmp/_odoo_contact_preview.html`,
`tmp/_make_contact_preview.py`, `__pycache__`.
