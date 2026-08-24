# PolySaaS Active Handoff

<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Slack producer/consumer home — 2026-08-24 -->

This file is the canonical startup and end-of-day handoff for the repo.
Every agent — Copilot, Cursor, and Windsurf — must read it before work.

## Status

- Date/session: 2026-08-24 — **BINGO** Slack home + producer/consumer pairing
- Branch: `cursor/polysniffer-slack-native-capture`
- Cert: `documentation/BINGO_SLACK_PRODUCER_CONSUMER_2026-08-24.md` (`28b07da0`)
- Agent sync check: passed
- Tenant of record: **OLIENTR** (Odoo + Slack)
- GOLD ZIP: `D:\BINGO ZIPS\BINGO_slack_producer_consumer_2026-08-24.zip` (create if missing — BINGO ritual)

## BINGO (this session)

Allowlisted Slack contact/sale producers pair to Odoo consumers. Slack Browse is
real top-level Slack (no iframe). Empty bookmark rail stays hidden. Mailbox
plumbing already in. See BINGO doc for certified / not-this-bingo.

**Slack popups / green-bar instruction-match copy — done (after BINGO).**
Frozen BINGO source files were not edited.

## After BINGO (2026-08-24)

- Shared bar shows instruction-match copy (`POST REQ <path> → consumer`).
- Slack contact/sale popups remain Slack-shaped overlays with required labels.
- Mailbox results now include `executescript` for bar/consumer naming.
- 21 focused tests passed. Interactive browser click-through still needs a
  signed-in hard-refresh after Waitress restart.

**Next:** more Slack popup/orch polish only if Michael asks; do not reopen
producer/consumer pairing or Browse.

## Sequence still locked

Native HAR → passthrough → pair producers to consumers → popups/orch UX.

## Blockers / risks

- Coordinated migrate still blocked at legacy `dose.0028_mlprompt`. Do not fake
  without an audited plan.
- After pull: restart Waitress + hard-refresh endpoint homes.

## Commit exclusions

**Exclude:** `documentation/Capital Raise Project/**`, `polysniffer-auth.json`,
`polysniffer_evidence/`, `tmp/_probe_*`, `__pycache__`.
