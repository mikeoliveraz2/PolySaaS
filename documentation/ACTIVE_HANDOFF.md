# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.
Every agent — Copilot, Cursor, and Windsurf — must read it before work.

## Status

- Date/session: **2026-08-26 EOD — office → Canada (laptop)**
- Michael is traveling to Canada. Next session is the **laptop**.
- Branch: `cursor/polysniffer-slack-native-capture`
- HEAD (pushed): `8c218f2f` — *Make the endpoint-home title readable and add create-orchestration actions.*
- Also on this branch (already pushed): `1b7128f9` merge of morning laptop polish + local Mattermost mark; `3b31ee79` morning polish; `842afaba` Mattermost sidebar PNG.
- Prior BINGO certs (still frozen unless owner unlocks):
  - `documentation/BINGO_SLACK_ODOO_FORMS_2026-08-25.md` (`b28be615` / hash note `6855e679`)
  - `documentation/BINGO_SLACK_PRODUCER_CONSUMER_2026-08-24.md` (`28b07da0`)
- Agent sync check: passed (`python scripts/check_agent_sync.py`)
- Tenant of record: **OLIENTR** (also probe `olient` / `polysaasonline`)
- Not a BINGO commit

## Completed this office session (2026-08-26)

1. **Pulled/merged morning laptop work** (`3b31ee79`): PNG app marks, per-app producer/consumer scoping, Slack sale partner-name fix, empty producer/consumer panels hidden.
2. **Endpoint-home header name** (owner: next to the icon, **not** the sidebar). Title + description were present but near-invisible on the white content pane. Now dark/bold via `endpoint_home.css?v=20260826-4`. Sidebar/Jazzmin card layout was **not** changed (mistaken sidebar pass reverted).
3. **Create-orchestration row** on every endpoint home (under the header, above existing bookmarks):
   - New producer → Add Instruction `?app=<key>&role=producer`
   - New consumer → Add Instruction `?app=<key>&role=consumer`
   - Dynamic service based on API → Add Instruction `?app=<key>&custom_endpoint=1`
   - Dynamic service → Add Atomic Service
   Query params `role=` / `custom_endpoint=1` are **not yet consumed** by `InstructionAdmin` — all three Instruction links currently open the same add form (app-filtered). Dynamic service is the only distinct destination.
4. Tests: `dose.tests.test_endpoint_home` green (12 tests).
5. Pushed office work: `8c218f2f` (and the two earlier local commits).

## Files (office UI pass)

- `dose/templates/dose/endpoint_home.html` (+ `.bak`)
- `dose/static/admin/css/endpoint_home.css` (+ `.bak`)
- `dose/tests/test_endpoint_home.py` (+ `.bak`)

## WIP / not finished

- **Odoo Invoices bookmark → CallBackData**: stub `dose/services/odoo_list_invoices.py` exists; adapter/bookmark wiring and UI not done. Do not treat as live.
- Create-orchestration buttons are **links only**. They do not yet create a producer row, prefill Custom Endpoint URL, or return to endpoint home after save.
- Optional: square Odoo mark if wide PNG looks cramped in the 52px sidebar tile.

## Next (Canada / laptop)

1. `git pull origin cursor/polysniffer-slack-native-capture` then `.\runall.ps1` (one Waitress + one mailbox consumer).
2. Hard-refresh endpoint homes (`endpoint_home.css?v=20260826-4`). Confirm **Odoo** (and Slack) show the name to the **right of the header icon**, plus the four create chips under the header.
3. Verify Slack New sale with reused email + different customer name lands on that name in Odoo (mailbox consumer must be running).
4. Finish Odoo **Invoices** bookmark → list invoices into CallBackData (wire adapter; do not invent Mattermost/HubSpot fillers).
5. If owner wants the create chips to actually differ: teach `InstructionAdmin.get_changeform_initial_data` to honor `role=` / `custom_endpoint=1`. Ask first — `admin.py` is BINGO-frozen.

## Leave alone (owner)

- Browse buttons / orch READY strip / Pair-Run pattern already BINGO-frozen unless unlocked.
- Do not invent Mattermost webhooks to fill empty homes.
- Do not restyle producer/consumer cards in the invoices pass.
- Do not put passthrough **names** into the sidebar as a substitute for the endpoint-home header (already done in the header).

## Sequence still locked

Native HAR → passthrough → pair producers to consumers → popups/orch UX.

## Blockers / risks

- Coordinated migrate still blocked at legacy `dose.0028_mlprompt`. Do not fake without an audited plan.
- Multiple Waitress/mailbox processes can accumulate — prefer one Waitress + one mailbox consumer after `runall.ps1`.
- Frozen endpoint-home files were owner-unlocked **only** for header contrast + the create row. Further edits still need a fresh ask.

## Commit exclusions (this EOD)

**Exclude:** `documentation/Capital Raise Project/**`, `polysniffer-auth.json`,
`polysniffer_evidence/`, `tmp/_probe_*`, `tmp/_smoke_*`, `tmp/waitress_err.txt`,
`tmp/_make_contact_preview.py`, `tmp/_make_mm_sidebar_icon.py`, `tmp/_odoo_contact_preview.html`,
`Lesson1.py`, `mona1.py`, `dose/templates/admin/includes/custom_sidebar_head.html.bak` (leftover from reverted sidebar experiment; live sidebar file is clean),
`templates/jazzmin/admin/index.html.bak`, `__pycache__`, unused SVG logo drafts unless referenced.
