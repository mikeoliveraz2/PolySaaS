# PolySniffer Native → Forwarder → Handler

**Status: LOCKED north star (owner-approved plan 2026-08-21)**

Agents must not invent Native as an external Chromium/plain-browser session. Native traffic crosses the forwarder so HARs match what a handler will later proxy.

## Two modes (same workspace shell)

| Mode | Browse URL | Green orchestration bar | Purpose |
|------|------------|-------------------------|---------|
| **Native** | `/admin/polysniffer/sniff/<host>/native/...` | **No** | Discovery HAR through forwarder (cookies, headers, bodies, assets) |
| **Passthrough** | `/admin/polysniffer/sniff/<host>/workspace/passthrough/...` | **Yes** | Product look-and-feel + **Insert Orchestration** / bind action path → consumer |

Slack Native must look like every other Native: no green bar. The bar and consumer-bind UI meet only on Passthrough.

Do **not** launch Native via `/pt/polysniff/` — that path is passthrough-mode and carries the bar.

## Intent

```
User (workspace pane)
  → Native browse through forwarder /admin/polysniffer/sniff/<host>/native/
  → Upstream app
  → Forwarder strips/relays
  → TrafficLog / HAR (cookies, headers, bodies, assets, redirects)
  → Enough evidence → app handler + Passthrough
  → Passthrough: green bar + attach action path → webhook/consumer
  → Orchestration bar (DoseMessage)
```

## Locked rules

1. **Native is discovery**, not the finished product embed. Success metric = richest unmodified HAR possible while the user walks the normal app flow.
2. **Traffic must cross the forwarder.** Playwright / plain Chromium talking straight to upstream is invalid for Native (PolySniffer never sees the in-proxy HAR).
3. **Unified UI** across endpoints: same workspace shell (mode cards, browse pane, Live capture, Diff/Export). Handler differences stay behind the boundary.
4. **Passthrough is built from Native evidence** (rewrites, cookie relay, CSP, auth shim, wrap gates). Mode may range from HTML scrape to API-only; attach-orchestration gesture stays the same.
5. **Orchestration attach** binds webhook → consumer (mailbox), not “run atomic inside the browse HTTP request.” Feedback = DoseMessage / bar.
6. **No iframes, and no `<object>`** (see `AI_RULES.md` / `passthrough-no-iframes.mdc`). The Native pane is an **inline embed**: the forwarder's HTML is mounted directly into the workspace document. Do not reintroduce a nested browsing context of any kind without a written owner exception.

## Rejected

- Default Native = external Chromium (`native_browser_capture.py` / top-level-only launch).
- “Open real Slack outside the proxy” **inside** PolySniffer Native.
- Hardcoding app-specific rules into shared forwarder (handler isolation).
- **Rendering the Slack UI as the product** — by frame or by proxy (2026-08-21, owner). See Slack note.

## Forwarder invariants (proven 2026-08-21 — do not regress)

These are generic proxy correctness, not app-specific. Each cost a live debugging round.

1. **Never copy hop-by-hop headers onto the response.** `Transfer-Encoding`, `Connection`, `Upgrade`, etc. are forbidden by PEP 3333; Waitress raises `AssertionError` and a healthy upstream 200 reaches the browser as a 500 served as `text/html`. Also drop `Content-Encoding` / `Content-Length` — `requests` already decoded, Django recomputes.
2. **Relay `Set-Cookie` individually, rewritten for the proxy origin.** `dict(resp.headers)` comma-joins multiple cookies into one broken header, and upstream `Domain=<upstream>; Secure` can never be stored on the PolySaaS host. Drop `Domain`, drop `Secure` on plain HTTP, downgrade `SameSite=None` → `Lax`. Without this an app waits forever for a session cookie that cannot arrive.
3. **Capture must never break the product.** HAR capture is observation. Binary bodies decode to text containing NUL, which PostgreSQL rejects outright (`A string literal cannot contain NUL (0x00)`), so capture receives a scrubbed copy and the call is wrapped — a bad HAR row must not 500 a healthy response.
4. **PolySaaS-owned URLs are never rewritten by an injected shim.** Anything under `/admin/polysniffer/sniff/` belongs to us; rewriting it sends the workspace's own Live-capture poll upstream and produces a CORS/404 flood.

## Inline embed invariants (browser side)

1. **Restore the upstream root element.** Inline embedding carries head and body only, so `<html>` and its attributes are lost. Apps keep real configuration there — Slack's CDN base is `<html data-cdn="https://a.slack-edge.com/">`, and without it the SPA requests its bundles from us. Re-apply `data-*` / `lang` / `dir` to `document.documentElement` **before** upstream scripts run.
2. **Strip upstream CSP `<meta>`.** A hash-allowlist CSP blocks every injected shim.
3. **CDN assets load direct.** Precedent: `hubspot_native_sniff`. Only app paths go through the proxy.
4. **`location` navigations cannot be intercepted.** `Location` members are `[LegacyUnforgeable]` in WebIDL — own, non-configurable properties per instance — so patching `Location.prototype` is silently ignored. `fetch`, `XHR`, and element attributes are interceptable; a real navigation is not. Any recovery from a stray upstream path must be **server-side**.

## Slack note

- **PolySniffer Native** may proxy Slack for **discovery HAR capture** only.
- **The Slack UI will not be rendered inside PolySaaS** — not framed, not proxied (owner decision, 2026-08-21). Proven live: with assets and the auth iframe both working, Slack reached `[AUTH] credentials are ready`, then waited on a first-party `lc` cookie it will only accept from `slack.com` and fell back to a top-level `/auth` redirect. The Slack client requires first-party `slack.com` cookies; no proxy can supply them.
- **The Slack product is composition, not framing:** PolySaaS orchestration bar on our origin, real Slack in its own window or desktop app — two surfaces, one operator experience.
- **Production Slack orchestration** remains API-first: slash command → webhook mailbox → consumer (`POLYSAAS_ORCHESTRATION_MODEL.md`). Native sniff does not replace that path.

## Entry URLs

- Workspace: `/admin/polysniffer/sniff/<host>/`
- Native shell (document navigations): `/admin/polysniffer/sniff/<host>/workspace/native/…`
- Native proxy (fetch / XHR / assets): `/admin/polysniffer/sniff/<host>/native/…`
- Tenant is carried as `?_ps_tenant=<schema>` — **never** `?schema=`, which upstream apps consume as their own parameter. Strip both before forwarding.
- Do not launch Native via `/pt/polysniff/` (passthrough-mode, carries the bar) or via endpoint-id polysniff URLs

## Related files

- Capture: `dose/polysniffer/har_capture.py` (**frozen**)
- Native forward: `dose/polysniffer/sniff_forward.py` (often frozen — ask before edit)
- Inline embed: `dose/polysniffer/sniff_native_embed.py`
- Native rewrites / header filter: `dose/polysniffer/sniff_native_rewrite.py` (**frozen**)
- Host-keyed proxy: `dose/polysniffer/sniff_pt_proxy.py`, `pt_polysniff_urls.py`
- Workspace UI: `dose/templates/polysniffer/sniff_workspace.html`
- Orchestration model: `documentation/POLYSAAS_ORCHESTRATION_MODEL.md`

## Open advisory

`xframe_options_exempt` predates the no-framing decision in `sniff_pt_proxy.py`,
`pt_polysniff_urls.py`, and `views/proxy.py`. Untouched, pending an owner call on
whether no-framing is project-wide.
