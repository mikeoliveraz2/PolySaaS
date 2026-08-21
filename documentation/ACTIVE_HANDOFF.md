# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.

Every agent — Copilot, Cursor, and Windsurf — must read this file at the start of every session.

## Status

- Date: 2026-08-21
- Repo state: synchronized with current main branch (after this push)
- Latest validated handoff: this file
- Policy: end-of-day work requires a handoff update before the final commit is considered complete
- Branch: `main`
- Machine: laptop session → push for office pickup

## Last session summary (2026-08-21)

Slack PolySniffer native-pane work (still OPEN — pane not settled). Large progress on proxy-relay auth path and host-keyed polysniff URLs.

### What landed this session

1. **Host-keyed `/pt/polysniff/`** — dropped redundant endpoint id.
   - Before: `/pt/polysniff/4/...`
   - After: `/pt/polysniff/app.slack.com/...`
   - Aligned with `/pt/admin/<host>/` and workspace `/admin/polysniffer/sniff/<host>/`.
   - Files: `pt_polysniff_urls.py`, `sniff_pt_proxy.py`, `sniff_workspace.html`, `sync_session.py`, HubSpot URL helpers, `client_snippets.py`, `sniff_pt_embed.py`, `workspace_pt_redirect.py`, `sniff_v2.py`.

2. **Slack passthrough handler** (`dose/passthrough/handlers/slack_handler.py`) — major work:
   - Proxy-relay model (do not rewrite `/auth` direct to `app.slack.com`; keep traffic through our proxy so cookie relay + CSP strip apply).
   - Host-root `/auth` via `upstream_url_for_subpath` (Nextcloud-style origin+path) — stops stacking `/auth` under deep client URLs.
   - Renamed tenant launch param from `?schema=` to `?_ps_tenant=` (Slack’s own `schema` query is numeric; our value caused `lc cookie (NaN)`).
   - Cookie-aware path + CSP strip coordination with polysniff proxy.
   - `postMessage` bridge: patch `window` / `parent` / `top` / `Window.prototype` so auth iframe `postMessage(..., 'https://app.slack.com')` retargets to proxy origin (`localhost:8000`). Confirmed live: `[SLACK SHIM] postMessage(parent) … -> http://localhost:8000`.
   - In progress (unverified after last edit): spoof parent `MessageEvent.origin` to `UPSTREAM_ORIGIN` + wrap `window.onmessage` — parent still timed out after successful postMessage (“fetching credentials from iframe took too long”).

3. **`handler_base.py`** — `requires_top_level_native()` default False; Slack no longer forced to top-level tab for Native.

4. **Workspace / core** — `_ps_tenant` threaded alongside schema for admin / launch links.

### Live state at handoff (OPEN — not BINGO)

- Endpoint: Slack `app.slack.com` under tenant `olient`
- Native pane loads host-keyed proxy; `/` and `/auth` return 200
- Auth iframe reaches “credentials are ready”; postMessage rewrite works
- Parent still falls back after ~30s → redirect to `/auth`; pane remains blank
- Beacon to `dev.slack.com` fails (noise, not the primary blocker)
- Server: Waitress via `runall.ps1` (no autoreload) — restart after pulling this commit before testing MessageEvent spoof

### Architectural stance (do not regress)

- Forwarder is a black box: browser ↔ our proxy ↔ Slack; Slack must not see “behind” the proxy.
- Passthrough look/feel should match other apps; Native may differ only when an app cannot embed.
- No iframes-as-default for SPAs; current workspace uses `<object>` (same pattern as Odoo/Mattermost sniff).

## Critical local facts for office machine

- Restart services after pull (`runall.ps1` / Waitress) — code changes do not hot-reload.
- Test URL shape: `/pt/polysniff/app.slack.com/?_ps_tenant=olient` (not `/pt/polysniff/<id>/`, not `?schema=` for Slack launch).
- Watch DevTools console for `[SLACK SHIM] postMessage(...)` and whether parent still times out on credential iframe.
- Do **not** mark BINGO until native pane shows Slack UI with screenshot proof.

## Current priorities

1. Finish/verify MessageEvent origin spoof so parent accepts credentials and UI settles.
2. Keep host-keyed polysniff as the only launch path.
3. Maintain rule sync + handoff discipline across machines.

## Current blockers

- Slack native pane blank after auth credential handoff (parent message-origin / timeout path). MessageEvent spoof written but **not proven** in browser after last edit.

## Next actions (office / next session)

1. `git pull origin main` then restart Waitress.
2. Open PolySniffer workspace for Slack → Native mode → left pane.
3. Confirm MessageEvent spoof: credentials apply and pane renders (or capture next failure: Network + Console).
4. If settled: screenshot + decide BINGO vs further shim polish.
5. Do not re-add team-slug / Mattermost team logic; do not rewrite Slack `/auth` direct off-proxy.

## Validation

- Host-keyed URL resolution exercised in session.
- Auth path: real small `/auth` response; credentials-ready observed.
- postMessage retarget confirmed in console.
- MessageEvent spoof: code present; browser proof pending after restart.

## Session files (this commit)

- `dose/passthrough/handlers/slack_handler.py` (+ `.bak`)
- `dose/passthrough/handlers/handler_base.py` (+ `.bak`)
- `dose/passthrough/handlers/hubspot_handler.py` (+ `.bak`)
- PolySniffer host-key + `_ps_tenant` path files listed above (+ `.bak` where created)
- This handoff + `COORDINATION_README.md`

## Explicitly excluded from commit

- `documentation/Capital Raise Project/*` (unrelated investor assets)
- `polysniffer-auth.json` (credentials)
- `polysniffer_evidence/` (local screenshots; not BINGO-certified)
- `dose/polysniffer/sniff_pt_proxy.py.bak_20260821_csp_strip_fix` (dated side backup; optional — include only if present as session bak)

## Process notes

- Piccolo Passo / bak-before-edit followed.
- Frozen-file exceptions used only with owner approval when applicable.
- Rule 6: no silent WIP — this push is the office handoff.
