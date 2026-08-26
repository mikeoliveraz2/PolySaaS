# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.
Every agent — Copilot, Cursor, and Windsurf — must read it before work.

## Status

- Date/session: 2026-08-26 — office handoff (laptop → office)
- Branch: `cursor/polysniffer-slack-native-capture`
- Prior BINGO certs (still frozen unless owner unlocks):
  - `documentation/BINGO_SLACK_ODOO_FORMS_2026-08-25.md` (`b28be615` / hash note `6855e679`)
  - `documentation/BINGO_SLACK_PRODUCER_CONSUMER_2026-08-24.md` (`28b07da0`)
- Agent sync check: passed
- Tenant of record: **OLIENTR** (also probe `olient` / `polysaasonline`)
- Not a BINGO commit — incremental polish + sale partner-name fix

## Completed this session

1. **App logos** — endpoint home header + sidebar tiles use PNG marks under `static/img/apps/` (Slack, HubSpot, Mattermost, Odoo). Helpers in `dose/endpoint_browser.py`.
2. **Per-app producer/consumer scoping** — Mattermost/Odoo homes no longer dump Slack allowlist or cross-app Instructions. Slack allowlist producers only on Slack home, and **only when Paired** (no unpaired futures). Empty Producers/Consumers panels are hidden (no placeholder copy).
3. **Slack → Odoo sale customer name** — `OdooCreateQuotation` prefers partner **name**; reuses email match only when names also match; otherwise creates a new partner (fixes Tom T Hall → Michael Oliver / My Company hijack). Mailbox consumer must be running for live sales.
4. Tests: `dose.tests.test_odoo_create_quotation` + `dose.tests.test_endpoint_home` updated/green.

## WIP / not finished

- **Odoo Invoices bookmark → CallBackData**: stub service `dose/services/odoo_list_invoices.py` exists; adapter/bookmark wiring and UI not done. Do not treat as live.
- Lists look/feel almost there; invoices bookmark still the open polish item from morning brief.

## Next (office)

1. Hard-refresh endpoint homes (`endpoint_home.css?v=20260826-2`); restart Waitress + `start_mailbox_consumer` after pull.
2. Verify Slack New sale with reused email + different customer name lands on that name in Odoo.
3. Finish Odoo **Invoices** bookmark → list invoices into CallBackData (wire adapter; do not invent Mattermost/HubSpot fillers).
4. Optional: square Odoo mark if wide PNG looks cramped in 52px tile.

## Leave alone (owner)

- Browse buttons / orch READY strip / Pair-Run pattern already BINGO-frozen unless unlocked.
- Do not invent Mattermost webhooks to fill empty homes.
- Do not restyle cards in the invoices pass.

## Sequence still locked

Native HAR → passthrough → pair producers to consumers → popups/orch UX.

## Blockers / risks

- Coordinated migrate still blocked at legacy `dose.0028_mlprompt`. Do not fake without an audited plan.
- Multiple Waitress/mailbox processes can accumulate on this machine — prefer one Waitress + one mailbox consumer after `runall.ps1`.

## Commit exclusions

**Exclude:** `documentation/Capital Raise Project/**`, `polysniffer-auth.json`,
`polysniffer_evidence/`, `tmp/_probe_*`, `tmp/_smoke_*`, `tmp/waitress_err.txt`,
`__pycache__`, unused SVG logo drafts unless referenced.
