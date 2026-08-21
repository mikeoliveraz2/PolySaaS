# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.

Every agent — Copilot, Cursor, and Windsurf — must read this file at the start of every session.

## Status

- Date: 2026-08-21
- Branch: `cursor/polysniffer-slack-native-capture`
- North star: `documentation/architecture/POLYSNIFFER_NATIVE_FORWARDER.md`
- Agent sync: passed

## Implemented this session (Native → Forwarder → Handler plan)

### 1. Documented lock

- `documentation/architecture/POLYSNIFFER_NATIVE_FORWARDER.md`
- `.cursor/rules/polysniffer-native-forwarder.mdc`
- `AI_RULES.md` §5 aligned (API-first production + Native discovery via forwarder)

### 2. Native through forwarder (code)

- **`sniff_session.py`**: Native session start **no longer launches Playwright**. Returns `browse_via=forwarder`. Capture is pane → `/pt/polysniff/<host>/`.
- **`sniff_workspace.html`**: Always embeds host-keyed polysniff in `<object>`; removed top-level upstream `window.open` bypass. Rich Live capture (headers/cookies/bodies) + **Mark action path** + Instruction draft link.
- **`sniff_v2_workspace.py`**: Poll returns full HAR-ish fields for Live capture.
- **`slack_handler.py`**: Stronger MessageEvent / parent `onmessage` spoof bridge.
- Regression test: `dose/tests/test_native_session_forwarder_only.py` (PASS).

### 3. HAR audit + handler-from-HAR docs

- `documentation/architecture/POLYSNIFFER_HAR_FIDELITY_AUDIT.md` (gaps; next enrichment = Set-Cookie → HAR cookies — needs owner go)
- `documentation/architecture/POLYSNIFFER_HANDLER_FROM_HAR.md`

### 4. Mailbox track (separate)

- Orchestration model updated with separation note (no clobber of API-first rules).
- Mailbox timezone compare fixed (`is_expired` / dequeue naive-UTC safe).
- Live `/poly` still **not** go-live until owner says go.

## Browser proof still required (after Waitress restart)

Waitress does not auto-reload. After restart:

1. Slack workspace → Start Native → pane must load `/pt/polysniff/app.slack.com/?_ps_tenant=…` (not external Chromium).
2. Confirm Live capture rows with headers/cookies.
3. Confirm MessageEvent spoof / auth settle (or capture next console failure).
4. No BINGO until screenshot of settled Slack UI in Native pane.

## Prior open item (unchanged until proven)

- Slack auth: credentials-ready + postMessage retarget worked; parent timeout / blank pane was last live failure before this code pass.

## Next actions

1. Owner: restart Waitress (`runall.ps1` or equivalent).
2. Prove Slack Native pane + Live capture.
3. Owner go on HAR enrichment A (response cookies) if desired.
4. Owner go on mailbox `/poly` live slice when ready.
