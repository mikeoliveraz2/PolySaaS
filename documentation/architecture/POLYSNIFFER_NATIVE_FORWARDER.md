# PolySniffer Native → Forwarder → Handler

**Status: LOCKED north star (owner-approved plan 2026-08-21)**

Agents must not invent Native as an external Chromium/plain-browser session. Native traffic crosses the forwarder so HARs match what a handler will later proxy.

## Intent

```
User (workspace pane)
  → Native browse through forwarder / host-keyed /pt/polysniff/<host>/
  → Upstream app
  → Forwarder strips/relays
  → TrafficLog / HAR (cookies, headers, bodies, assets, redirects)
  → Enough evidence → app handler + Passthrough
  → Attach orchestration at action paths (webhook → consumer)
  → Orchestration bar (DoseMessage)
```

## Locked rules

1. **Native is discovery**, not the finished product embed. Success metric = richest unmodified HAR possible while the user walks the normal app flow.
2. **Traffic must cross the forwarder.** Playwright / plain Chromium talking straight to upstream is invalid for Native (PolySniffer never sees the in-proxy HAR).
3. **Unified UI** across endpoints: same workspace shell (mode cards, browse pane, Live capture, Diff/Export). Handler differences stay behind the boundary.
4. **Passthrough is built from Native evidence** (rewrites, cookie relay, CSP, auth shim, wrap gates). Mode may range from HTML scrape to API-only; attach-orchestration gesture stays the same.
5. **Orchestration attach** binds webhook → consumer (mailbox), not “run atomic inside the browse HTTP request.” Feedback = DoseMessage / bar.
6. **No iframes** as default SPA embed (see `AI_RULES.md` / `passthrough-no-iframes.mdc`). Workspace uses `<object>` / host-keyed polysniff unless owner authorizes otherwise.

## Rejected

- Default Native = external Chromium (`native_browser_capture.py` / top-level-only launch).
- “Open real Slack outside the proxy” **inside** PolySniffer Native.
- Hardcoding app-specific rules into shared forwarder (handler isolation).

## Slack note

- **PolySniffer Native** may proxy Slack for **discovery HAR capture** (host-keyed `/pt/polysniff/app.slack.com/…`).
- **Production Slack orchestration** remains API-first: slash command → webhook mailbox → consumer (`POLYSAAS_ORCHESTRATION_MODEL.md`). Native sniff does not replace that path.

## Entry URLs

- Workspace: `/admin/polysniffer/sniff/<host>/`
- Native browse: `/pt/polysniff/<host>/…` with `?_ps_tenant=<schema>` when cross-tenant
- Do not use endpoint-id polysniff URLs as the primary launch path

## Related files

- Capture: `dose/polysniffer/har_capture.py`
- Native forward: `dose/polysniffer/sniff_forward.py` (often frozen — ask before edit)
- Host-keyed proxy: `dose/polysniffer/sniff_pt_proxy.py`, `pt_polysniff_urls.py`
- Workspace UI: `dose/templates/polysniffer/sniff_workspace.html`
- Orchestration model: `documentation/POLYSAAS_ORCHESTRATION_MODEL.md`
