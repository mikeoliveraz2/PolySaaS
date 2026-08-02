<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Mattermost slug identity + SSO Town Square working — 2026-08-02 -->

# BINGO: Mattermost Slug Identity + SSO Town Square Working

**Date:** 2026-08-02  
**Verified by:** Michael (live browser, tenant `pso17`) + agent  
**Commit:** `8100b79a` (`8100b79a11f6099841079b45ab87ecc88b6f5277`)

## What this certifies

Mattermost passthrough for tenant **pso17** loads Town Square end-to-end under the PolySaaS admin shell:

- URL identity is **`/pt/admin/<slug>/`** (and `/pt/dose/<slug>/`) from the DB `PassThroughEndpoint` row — not hostname-as-trigger
- Early fetch guard + full display shim both parse and run
- Auth: `GET /api/v4/users/me` → **200**, Bearer injected
- WebSocket connects to Mattermost origin (`ws://localhost:8065/...`)
- Static chunks / `/static/files/*` rewrite to upstream `:8065`
- Channel UI + system messages render; onboarding modal is normal Mattermost first-run UX

## Root causes fixed this session

### 1. Endpoint identity — slug, not trigger

Owner directive: the `PassThroughEndpoint` row **is** the endpoint. Menu/proxy URLs use `endpoint.slug`. Middleware resolves by slug; handler via `matches_endpoint(endpoint)`. Upstream comes only from `endpoint.endpoint_url`. Legacy `/pt/admin/localhost:8065/` bookmarks 302 → `/pt/admin/mattermost/`.

### 2. Display-shim SyntaxError (`Invalid regular expression flags`)

The display shim is an `fr"""` (raw f-string). Plugin-static regexes were written as `/\\/static\\/...`, which the browser parses as a regex that closes early → **SyntaxError**. That aborted the main shim (auth headers, cookies, full rewrites) while the early guard still ran — hence chunk redirects worked but APIs returned **401**.

**Fix:** In the `fr"""` block only, use JS-correct single backslashes (`/\./`, `/\/static\/.../`, `/^\/api\/v4\/teams\/name\/.../`).

### 3. Supporting passthrough plumbing

- Mattermost/Dolibarr/Odoo/Nextcloud prefix helpers use slug
- Dose-home embed path stays in URLconf (no Jazzmin wrap for `/pt/dose/` documents)
- Sidebar ready/not-ready visual contrast (green ready ring vs grayscale)
- Early guard v37: nested `/static/plugins/`, WS rewrite, Bearer on MM-origin fetch

## Live verification (Michael console, 2026-08-02 ~10:34)

```
[PolySaaS MM] Early fetch guard installed (v37)
[PolySaaS MM] shim build 2026-06-12-theme-sync
[PolySaaS Shim] Auth ready → staying on full shell
[PolySaaS MM] users/me HTTP status: 200 OK
[PolySaaS Mattermost] WebSocket direct to MM server: ws://localhost:8065/...
[PolySaaS MM] XHR: GET /static/files/...css -> http://localhost:8065/static/files/...
```

Screenshot confirmed: Town Square + PolySaaS Dev Team under orchestration bar, tenant **PSO17**.

## Known non-blockers (not part of this BINGO)

- `mattermost-ai` plugin: `users/username/ai` **404** (bot user not provisioned)
- PolySaaS passthrough plugin diagnostics **404** (plugin not deployed locally)
- Browser-extension “message channel closed” noise on `/admin/`

## Files in this commit

| Path | Role |
|------|------|
| `dose/passthrough/handlers/mattermost_handler.py` | Early guard + display shim regex fix; proxy prefix from slug |
| `dose/passthrough/middleware.py` | Resolve by slug; dose-home shell gate |
| `dose/passthrough/registry.py` | Endpoint-based handler resolve |
| `dose/passthrough/handlers/handler_base.py` | Prefix helpers from slug |
| `dose/passthrough/handlers/odoo_handler.py` | `matches_endpoint` / prefix via slug |
| `dose/passthrough/handlers/nextcloud_handler.py` | Same |
| `dose/passthrough/handlers/dolibarr_handler.py` | Same |
| `dose/passthrough/local_dev_registrations.py` | Emptied (obsolete for discovery) |
| `dose/models/pass_through_endpoint.py` | `get_menu_url` / `get_proxy_prefix` → `/pt/admin/<slug>/` |
| `dose/context_processors.py` | Menu URLs from slug |
| `dose/views/main.py` | `/pt/dose/<slug>/` embed helpers |
| `dose/odoo_sso_api.py` | Slug-aware paths |
| `dose/polysniffer/views/mattermost_static_proxy.py` | Slug-aware static proxy |
| `mysite/urls.py` | `<slug>` URL kwargs |
| `mysite/external_passthrough_middleware.py` | Aligned with slug identity |
| `dose/templates/admin/includes/custom_sidebar.html` | Ready/not-ready cards |
| `dose/templates/admin/includes/custom_sidebar_head.html` | Ready/not-ready CSS |
| `*.bak` | Pre-edit backups (bak-before-edit) |
| `documentation/BINGO_MATTERMOST_SLUG_IDENTITY_SSO_WORKING_2026-08-02.md` | This certification |

## Freeze

Every source file above carries:

```
THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
```

plus a `BINGO: Mattermost slug identity + SSO Town Square working — 2026-08-02` line.

## GOLD ZIP

`D:\BINGO ZIPS\BINGO_MATTERMOST_SLUG_SSO_<YYYY-MM-DD>.zip` (created after push; retain max 4 GOLD zips).
