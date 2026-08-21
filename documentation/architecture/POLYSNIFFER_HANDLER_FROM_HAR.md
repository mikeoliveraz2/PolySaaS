# Building passthrough handlers from Native HAR

**North star:** `POLYSNIFFER_NATIVE_FORWARDER.md`

## Process

1. Run Native (forwarder) until Live capture covers login + one happy-path action.
2. Export HAR / review TrafficLog for the endpoint host.
3. Identify families: HTML shells, static assets, API JSON, auth cookies, redirects, CSP.
4. Implement **only** in the app handler (`dose/passthrough/handlers/<app>_handler.py`):
   - `matches_endpoint`
   - HTML rewrite / shim
   - `upstream_url_for_subpath`, cookie relay, CSP coordination hooks
   - wrap/process gates
5. Never hardcode app names in `forwarding.py`, middleware, or registry branching.
6. Diff Native vs Passthrough with workspace Diff tool; close gaps one path family at a time.

## Slack (current)

- Handler: `dose/passthrough/handlers/slack_handler.py` (proxy-relay; keep `/auth` on-proxy).
- Open: MessageEvent origin spoof proof in browser after Waitress restart.
- Production events: API-first mailbox — not this handler.

## Unified UI

Mark action paths in Live capture (“Mark action path”) for later webhook → consumer bind. Same gesture for every endpoint.
