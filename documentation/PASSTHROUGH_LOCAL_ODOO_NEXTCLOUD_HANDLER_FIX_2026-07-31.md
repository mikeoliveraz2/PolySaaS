# Passthrough: Local Odoo/NextCloud Handler Resolution Fix — 2026-07-31

## Summary

Local dev passthrough for Odoo (`localhost:8086`) and NextCloud (`localhost:8888`) was
rendering as raw, unstyled HTML — no CSS, no login form styling, no SSO cookie
injection. Root-caused and fixed across three small, independent issues.

## Issue 1 — `middleware.py` forwarded a guessed URL before resolving the real one

`run_pt_admin_passthrough_core()` built a best-effort guessed `endpoint_url` from the
`/pt/admin/<trigger>/` URL segment, then only looked up the authoritative
`PassThroughEndpoint` record *after* the early-shell handler hook had already run
against the guess. Fixed by resolving the real `PassThroughEndpoint` via a direct,
exact `netloc` match (matching how `PassThroughEndpoint.get_menu_url()` builds that
same segment) **once, up front** — before any handler hook, so every code path sees
the same authoritative URL from the start. The old second-pass `icontains` override
block was removed as redundant. The trigger-guess `SimpleEndpoint` remains only as a
DB-unavailable / not-yet-provisioned fallback.

See inline comment in `dose/passthrough/middleware.py` (SECURITY/CORRECTNESS FIX
2026-07-31).

## Issue 2 — No handler ever matched the local endpoints

Even with the correct `PassThroughEndpoint` resolved, `OdooPassthroughHandler.
matches_endpoint()` only checks for the substring `'odoo'` in `endpoint_url`. The
local dev URL (`http://localhost:8086`, per `documentation/LOCAL_STANDALONE_STACK.md`'s
fixed local port map) contains no such string, so the handler was never selected —
meaning `process_html_response()` (asset URL rewriting, cookie handling, SSO
injection) never ran, producing the raw/unstyled page.

Fixed without touching any frozen handler file: `dose/passthrough/registry.py`
already has an unused, explicit `register_handler(trigger, handler_class)` /
`get_handler(trigger)` mechanism that `resolve_handler_for_pt_admin_trigger()` checks
*before* any fuzzy `matches_endpoint()` guessing. Added
`dose/passthrough/local_dev_registrations.py` (new file) to populate that registry
explicitly for local dev:

```python
"localhost:8086" -> OdooPassthroughHandler
"localhost:8888" -> NextcloudPassthroughHandler
```

Wired in via one added import line in `dose/signals.py` (already imported by
`DoseConfig.ready()`). No changes to `registry.py`, `odoo_handler.py`, or
`nextcloud_handler.py`. Production endpoints (e.g. `polysaas-odoo2.onrender.com`)
are unaffected — they already match via the existing `'odoo' in url` heuristic since
the hostname itself contains "odoo".

## Issue 3 — `starting_uri` baked a path into the "base" endpoint (data, not code)

The local `PassThroughEndpoint` records had `starting_uri` set to `/web` (Odoo) and
`/index.php/login` (NextCloud), which `dose/context_processors.py` appends onto the
sidebar link. This hardcodes an assumption about the app's entry path into what
should be a bare base URL — the upstream app's own root redirect is what's supposed
to determine that path (both `OdooPassthroughHandler` and the passthrough forwarder
already follow upstream GET redirects). Fixed by clearing `starting_uri` to blank on
both local records (`olient` schema, ids 1 and 2) — a data change only, no code
touched, no migration needed, takes effect immediately (no server restart required).

## Status

Verified locally: handler now resolves to `OdooPassthroughHandler` for
`localhost:8086`; sidebar links render bare-base; Odoo login page renders styled with
CSS applied after server restart. Not yet declared a BINGO/frozen milestone — treat
as a regular fix pending further testing.
