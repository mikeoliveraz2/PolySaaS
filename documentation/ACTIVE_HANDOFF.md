# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.

Every agent — Copilot, Cursor, and Windsurf — must read this file at the start of every session.

## Status

- Date: 2026-08-21
- Branch: `cursor/polysniffer-slack-native-capture`
- North star: `documentation/architecture/POLYSNIFFER_NATIVE_FORWARDER.md`
- Agent sync: passed
- Tests: `test_slack_native_sniff` + `test_polysniffer_architecture` = 31 pass
- `python manage.py check`: no issues
- Waitress restarted after every change (it does not auto-reload)

## Owner decision this session (supersedes prior "prove Slack UI in pane" goal)

**Slack will not be rendered inside PolySaaS — no frame, no proxy of the Slack UI.**
Michael + Shela: the Slack scenario is **composition, not framing** — PolySaaS
orchestration bar on our origin, real Slack in its own window/desktop app.

The Slack product slice is:

1. `/poly` in Slack → ack + mailbox + consumer + bar
2. Bind UI: attach consumer to that webhook
3. Consumers: create contact, create sale
4. Record demo: Slack command → Odoo rows → bar update

Native mode keeps its real job: **forwarder capture for discovery (HAR evidence)**.
Whether the Slack UI ever paints in the pane is explicitly not a goal.

## Session work — Slack Native inline embed (five real bugs)

Each was a distinct root cause found from live console + `debug.log` tracebacks.

1. **Proxy 500 on every asset** — `sniff_forward.py` copied upstream
   `Transfer-Encoding: chunked` onto the WSGI response; Waitress raises
   `AssertionError: transfer-encoding is a "hop-by-hop" header` (PEP 3333), so a
   healthy upstream 200 surfaced as 500 + `text/html` MIME errors. Now strips the
   hop-by-hop set plus `content-encoding` / `content-length`.
2. **Assets requested from our origin** — inline embed drops `<html>`, and Slack
   keeps its CDN base on `<html data-cdn="https://a.slack-edge.com/">`. Firewall
   shim now re-applies the upstream root element's `data-*` / `lang` / `dir` to
   `document.documentElement` before Slack boots. CDN bundles load direct
   (same precedent as `hubspot_native_sniff`). Result: `[WD] … s: 7; f: 0`.
3. **Shim hijacked our own Live-capture poll** — `/admin/polysniffer/sniff/…/workspace/poll/`
   was rewritten into the native proxy and forwarded upstream (CORS + 404 flood).
   Shim now treats anything under `/admin/polysniffer/sniff/` as PolySaaS-owned.
4. **`PermissionError` saving session (Windows)** — `MIDDLEWARE` listed **both**
   `DebugSessionMiddleware` (which subclasses `SessionMiddleware`) **and** Django's
   `SessionMiddleware`, so each response saved the same session file twice and the
   writes raced. Removed the duplicate stock entry. `admin.E410` detects session
   middleware by subclass, so `manage.py check` still passes. Sessions stay on the
   file backend; nobody is logged out.
5. **`/beacon/timing` 500** — HAR capture decoded a binary body to text, and
   PostgreSQL rejects NUL: `ValueError: A string literal cannot contain NUL (0x00)`.
   `har_capture.py` is FROZEN, so the fix is forwarder-side: capture receives a
   NUL-scrubbed copy (`_CaptureSafeResponse`), browser bytes untouched, and the
   capture call is wrapped so a bad HAR row can never 500 a healthy response.

Also: **upstream cookie relay**. Slack returns `Domain=.slack.com; Secure` cookies
and the forwarder comma-joined multiple `Set-Cookie` headers into one. Cookies are
now re-issued individually for the proxy origin (drop `Domain`, drop `Secure` on
plain HTTP, downgrade `SameSite=None` → `Lax`). Generic proxy correctness, kept.

### Reverted deliberately

`django_resp.xframe_options_exempt = True` was added so Slack's **own** credential
iframe (`fetchAuthAndReturnToUrl: fetching credentials with iframe at /auth?…`)
would not be blocked by our own `XFrameOptionsMiddleware`. **Owner rejected it** —
removed, with its test assertion. Do not re-add without a written exception.

## Evidence captured (before the no-framing decision)

- Live capture recorded `/`, `/auth`, `/beacon/timing` ×2 — all **200**.
- Slack booted: all 7 gantry bundles loaded, watchdog reload loop gone.
- Auth handshake reached `[AUTH] credentials are ready` + postMessage to parent.
- Parent then waited on the `lc` cookie and fell back to a top-level `/auth`
  redirect → 404. Confirms Slack needs first-party `slack.com` cookies, which is
  exactly why framing/proxying the Slack UI is a dead end.

## Files changed

`dose/polysniffer/sniff_forward.py`, `dose/polysniffer/handlers/slack_native_sniff.py`,
`dose/polysniffer/sniff_native_embed.py`, `dose/polysniffer/sniff_urls.py`,
`dose/polysniffer/views/sniff_v2_workspace.py`,
`dose/templates/polysniffer/sniff_workspace.html`, `dose/admin.py` (`_ps_tenant=`),
`mysite/settings.py`, plus `dose/tests/test_slack_native_sniff.py` and
`dose/tests/test_polysniffer_architecture.py`. `.bak` files alongside each.

## Blockers / advisories

- **Known dead end (documented, not a bug):** the shim's `Location.prototype`
  patch cannot work. `Location` members are `[LegacyUnforgeable]` — own,
  non-configurable properties per instance — so a prototype patch is silently
  ignored. Real `location` navigations can never be intercepted from inside the
  page; any such recovery must be server-side.
- **Advisory (needs owner call):** `xframe_options_exempt` already exists in older
  modules — `dose/polysniffer/sniff_pt_proxy.py`, `pt_polysniff_urls.py`,
  `views/proxy.py`. Predates this session, untouched. If no-framing is project-wide
  policy, these want an audit.
- `DebugSessionMiddleware` swallows any session-save failure and returns the
  response anyway, so writes can be lost silently. It masked bug 4. Left as-is.

## Next actions

1. Verify `/poly` live end-to-end: ngrok URL registered on the Slack app,
   `signing_secret` + `slack_team_id` in `TenantApp.extra_config`, mailbox write,
   `start_mailbox_consumer` drain, bar update.
   Already built: `mysite/urls.py` → `hooks/slack/commands/`,
   `dose/views/slack_slash_command.py` (v0 signature, 300s replay window,
   tenant-by-`team_id`), `publish_slack_command_event` → `WebhookMailbox` (300s TTL),
   `dose/tests/test_slack_webhook_orchestration.py`.
2. Bind UI: attach a consumer to that webhook (existence not yet verified).
3. Consumers: `OdooCreatePartner` exists in the registry; "create sale" not found.
4. Record the demo: Slack command → Odoo rows → bar update.
