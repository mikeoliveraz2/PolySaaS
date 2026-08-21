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

## Evening addendum (2026-08-21) — navigation interception is impossible; relay is server-side

### Verified browser constraint (do not retry client-side navigation patching)

Probed in real Chrome via `tmp/_probe_location_patchability.py`:

```
window_location_descriptor: {'configurable': False, 'has_set': True, 'own': True}
redefine_window_location: threw: TypeError
location_proto_href: False          # Location.prototype.href does not exist
location_proto_assign: undefined
location_own_href_configurable: False
redefine_location_href: threw: TypeError
navigation_api: True
```

`window.location` and `Location`'s `href`/`assign`/`replace` are `[LegacyUnforgeable]`.
A page script **cannot** intercept `window.location = '/path'`. The old
`Location.prototype` patch block in `slack_handler.py` was therefore dead code and
has been removed. Only the Navigation API (Chrome-only) could intercept client-side.

### Why this mattered

After the credential iframe times out (~30s), Slack falls back to
`window.location = '/auth?...'`. That is root-absolute, so it landed on our origin
outside any proxy prefix, was never forwarded, and the pane stayed blank. The
console shows the fallback with **no** `[SLACK SHIM] proxy-relay rewrite` line,
which is the fingerprint of this class of bug.

### Fix shipped — generic stray-root-path relay (server-side)

- `dose/passthrough/stray_root_paths.py` (new) — aggregates an optional
  `stray_root_paths()` hook across discovered handlers, derives the proxy prefix
  from a **same-origin** `Referer`, returns the relay target. No app names.
- `dose/middleware/passthrough_stray_root_relay.py` (new) — 302s when a target is
  returned; otherwise passes through.
- `mysite/settings.py` — **one line** added to `MIDDLEWARE` (owner-approved frozen
  edit), placed before `ExternalPassthroughMiddleware`.
- `dose/passthrough/handlers/slack_handler.py` — declares `stray_root_paths()`
  returning `('/auth',)`; dead `Location.prototype` block removed.
- `dose/tests/test_stray_root_relay.py` (new) — 5 tests, all passing.

Handler isolation preserved: the base class and `registry.py` were **not** touched;
the hook is discovered via `getattr`, per the allowed pattern.

Verified through the real middleware stack:

```
claimed  /auth        -> 302 /pt/polysniff/app.slack.com/auth?app=client&return_to=...
no referer           -> 404 None
unclaimed path       -> 200 None
cross-origin referer -> 404 None
```

### Still open after this

- **Browser proof pending** — server must be restarted (Waitress, no autoreload)
  and the Native pane re-tested. The relay only removes the fallback dead-end; it
  does not prove Slack boots.
- The iframe credential handshake still times out for 30s before the fallback. The
  shim's own message probe is **self-blinded**: its capture-phase listener is
  registered through the patched `addEventListener`, so `spoofMessageEvent` rewrites
  `origin` before the log check runs. To learn whether `postMessage` actually
  delivers, save a native `addEventListener` reference before patching.
- `psc=NaN` still appears in `[AUTH] Need to re-fetch auth (... psc=NaN ...)`.

### Slack webhook slice recovered (separate track)

- `origin/cursor/polysniffer-switch-object-to-iframe` had been **deleted from the
  remote**; the local ref was the only copy. Preserved as
  `backup/slack-webhook-native-20260821` (`e8bbba50`).
- Surgical bring-over on `feature/slack-webhook-slice` (`e82fc259`): 9 files, zero
  overlap with `main`, 9/9 tests pass, route resolves at `/hooks/slack/commands/`.
  Awaiting Michael's review; **not merged**.
- Transport is **RabbitMQ**, not a "WebhookMailbox" — an emailed analysis had this
  wrong. Proving the pipe needs an active `MQConfig` (provider `rabbitmq`) in the
  tenant schema *plus* `slack_team_id`/`signing_secret`, or the view returns 503
  before Slack gets its ack.
- `main` was missing `dose/services/odoo_rpc.py`, required by `OdooCreatePartner`;
  included in the slice. `pika==1.3.2` installed on this laptop — the office
  machine needs it too.
- Fixed on `main` (`553f9b94`, owner-approved frozen edit): the orchestration toast
  poller in `display.html` read `data.unread_messages` while the live
  `UnreadDoseMessagesView` returns `messages`, so toasts never fired.

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
