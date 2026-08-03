# PolySaaS Coordination Log

This document tracks session activity across machines (laptop/desktop) for synchronization.

---

## 2026-08-03 (Morning — Office) — BINGO: Nextcloud server-side SSO ✅

**Status**: ✅ Verified for tenant `pso17` (Django test client SSO redirect + cookies)
**Branch**: main
**Doc**: `documentation/BINGO_NEXTCLOUD_SSO_WORKING_2026-08-03.md`

### Summary

1. Endpoint/nc_url → `http://localhost:8888`; user `pso17` created in shared NC; creds in `extra_config`.
2. Handler server-side form login SSO + `passthrough_early_shell_paths` so `/apps/files/` hits SSO.
3. Provisioner/settings: local URL rewrite, admin `admin`, `starting_uri=/apps/files/`, password sync on exists.

---

## 2026-08-02 (Late morning — Office) — BINGO: Mattermost slug identity + SSO Town Square ✅

**Status**: ✅ Live-verified for tenant `pso17` (Town Square + auth + WebSocket)
**Branch**: main
**Doc**: `documentation/BINGO_MATTERMOST_SLUG_IDENTITY_SSO_WORKING_2026-08-02.md`

### Summary

1. **Slug identity** — `/pt/admin/<slug>/` and `/pt/dose/<slug>/` resolve from DB
   `PassThroughEndpoint`; no hostname-as-trigger. Handler via `matches_endpoint(endpoint)`.
2. **Display-shim SyntaxError** — `fr"""` double-escaped `/\\/static\\/` regex aborted the
   main shim → APIs 401'd. Fixed to JS-correct single backslashes; Waitress restarted.
3. **Verified live** — Early guard v37 + full shim, `users/me` 200, WS to `:8065`, Town Square
   UI under orchestration bar (Michael screenshot + console).

Prior open item “Mattermost client stall” from the morning wrap-up is **closed** by this BINGO.

---

## 2026-08-02 (Morning — Office, session wrap-up) — Passthrough Fixes ✅ / Mattermost Client Stall ⚠️ PENDING _(superseded)_

**Status**: ✅ Backend/DB fixes complete and verified — ⚠️ live-browser Mattermost issue open _(resolved later same day — see BINGO above)_
**Branch**: main
**Commits pushed today (chronological)**: signup password security + Odoo trailing-slash BINGO,
dose-home passthrough (`get_current_tenant` search_path leak + `_endpoint_visible` fuzzy match)
+ Odoo anchor-click BINGO, Mattermost `PassThroughEndpoint` upsert fix (`6a783900`)

### Summary

Rule 6 in effect this session (never hold back WIP — see `process-rules.mdc`). Everything below
is committed and pushed to `main`; nothing sitting locally uncommitted.

1. **Signup password security** — removed plaintext password from debug log
   (`dose/subscription_views.py`), added Confirm Password field + client-side match validation
   to `dose/templates/dose/subscribe.html`. See `BINGO_SIGNUP_PASSWORD_SECURITY_AND_ODOO_TRAILING_SLASH_2026-08-02.md`.
2. **Odoo Invoicing 404/POST failures** — `mysite/urls.py` `pt/admin/`/`pt/dose/` subpath routes
   required a trailing slash, so Odoo's AJAX POSTs (no trailing slash) hit Django's
   `APPEND_SLASH` redirect and 500'd. Removed the mandatory trailing slash.
3. **Dose-home passthrough panel empty for every tenant** — root cause was `get_current_tenant()`
   in `dose/utils.py` flipping `search_path` to `public` for the Tenant lookup and never
   restoring it, so every tenant-scoped query for the rest of the request silently ran against
   `public`. Fixed with save/restore in a `finally` block. Compounding bug:
   `_endpoint_visible()` in `dose/views/main.py` used fuzzy hostname substring matching
   (`'odoo' in host`) which fails for `localhost:PORT` in local dev — replaced with explicit
   `endpoint.slug == TenantApp.app_name` matching. See
   `BINGO_DOSE_HOME_PASSTHROUGH_AND_ODOO_ANCHOR_FIX_2026-08-02.md`.
4. **Odoo "Activate Invoicing" 404 on bare `/odoo`** — native `<a href="/odoo">` clicks bypass
   all of the shim's patched `fetch`/`XHR`/`Location` functions. Added a capture-phase
   `click` listener in `dose/passthrough/handlers/odoo_handler.py` that rewrites anchor `href`
   before the browser navigates. Verified live by Michael — invoicing + dynamic orchestration
   confirmed working end-to-end.
5. **Mattermost never got a sidebar tile, for any tenant, ever** — owner unlocked the freeze on
   `dose/services/mattermost_tenant_provisioner.py` for this one fix
   ("unlock the freeze it was obviously wrong, fix it properly"). Root cause:
   `_ensure_passthrough_endpoint()`'s `update_or_create()` set `'name': 'Mattermost'`, but
   `PassThroughEndpoint` has no `name` field — every call raised, caught by a broad
   `try/except`, logged as a warning, and silently skipped, while the rest of provisioning
   (team/user/token) succeeded and reported success. Removed the bad key; `description` now
   reads `Mattermost Team Chat for {company/tenant name} (shared team: polysaas-dev-team)`,
   matching the convention already used by `odoo_tenant_provisioner.py`. Backfilled the missing
   row (without re-running Mattermost API provisioning) for `polysaas`, `pso13`, `pso14`,
   `pso16`. Verified via Django test client: `/dose/home/` for `pso16` now shows Mattermost
   alongside Odoo/NextCloud/HubSpot/Dolibarr (status 200), and a full click-through to
   `/pt/dose/localhost:8065/` returns a real 856KB Mattermost SPA shell (`<title>Mattermost</title>`),
   no redirect loop, no "Team Not Found". See
   `BINGO_MATTERMOST_PASSTHROUGH_ENDPOINT_FIX_2026-08-02.md`.

### ⚠️ Open issue — "Mattermost not responding" (reported live in browser, NOT yet reproduced/fixed)

After the endpoint fix above, Michael clicked into Mattermost in an actual browser and reported
it "not responding." All backend checks passed clean:
- Mattermost Docker container: healthy, port 8065 listening
- Direct `http://localhost:8065`: 200
- Passthrough proxy fetch (`/pt/dose/localhost:8065/`) via Django test client: 200, real HTML

Since a test client can't execute JS or open a WebSocket, this points to a **client-side stall**
in the injected shim (`dose/passthrough/handlers/mattermost_handler.py` — BINGO-frozen since
2026-05-31, ~5000 lines, heavy token/IDB/WebSocket bootstrap logic). Deliberately did NOT start
editing that file solo — it's frozen, huge, and specifically covered by
`.cursor/rules/mattermost-passthrough-no-team.mdc` (past unsupervised edits there caused
regressions).

### Next Session First Task

1. Open Mattermost via the sidebar in an actual browser, DevTools open (Console + Network tabs).
2. Identify exactly where it stalls: stuck spinner? console error? a specific XHR/WebSocket
   pending forever? token missing from IDB/localStorage/cookie?
3. Bring findings back before touching `mattermost_handler.py` — it's frozen, get Michael/Shela's
   sign-off on the specific fix before editing (per `bingo-freeze.mdc` / `process-rules.mdc`).

---

## 2026-05-29 (Morning — Condo) — Mattermost IDB Auth Fix ✅

**Status**: ✅ COMPLETE — committed and pushed  
**Branch**: main

### Summary
Fixed the Mattermost passthrough spinner/login loop. Root cause was that Mattermost uses **IndexedDB (localforage)** for redux-persist hydration, not localStorage. The shim was only writing to localStorage, which Mattermost never reads for auth bootstrapping.

### Fix
- Added `_writeTokenToIDB(token)` to the client-side shim — writes `persist:storage` into `localforage/keyvaluepairs` IDB with `entities.general.credentials` containing the token
- Added `_blockLoginAndRetry()` — on first `/login` intercept with valid token: writes IDB + does one page reload (sessionStorage-guarded to prevent loop)
- On reload, Mattermost finds token in IDB → hydrates Redux → `users/me` 200 → authenticated ✓

### Files Changed
- `dose/passthrough/handlers/mattermost_handler.py` (shim JS: IDB write, reload-once logic)

### Current State
- Mattermost passthrough works end-to-end: login bridge auto-submits → IDB written → one reload → Mattermost loads fully authenticated
- MMAUTHTOKEN cookie + localStorage also set as belt-and-suspenders
- `users/me` returns 200, plugin auth-check returns `valid: true`

### Next Session
- Monitor for token expiry / re-auth flow (stale token → IDB cleared → bridge re-runs)
- Pre-existing SQL bug: `invalid input syntax for type bigint: "polysaast97"` in orchestration hook — needs separate fix
- WebSocket is unproxied (direct to upstream) — acceptable for now

---

## 2026-05-27 (Evening — Office) — Final Wrap-Up ✅

**Status**: ✅ COMPLETE — all changes committed and pushed
**Branch**: main
**Commits**: `b3ce40c` (team cleanup), `76403ef` (login fix), `4642a17` (remove auto-submit)

### Today's Complete Session Summary
1. **Morning (Condo)**: Removed team specification from Mattermost redirects, preserved credentials across login via sessionStorage + API
2. **Evening (Office)**: 
   - Removed all `mm_team_name` references from handler and credential storage
   - Fixed login after subscribe by redirecting to `/dose/login/` (sets `search_path TO public`)
   - Removed auto-submit from Django login forms (user reviews credentials before clicking)
   - Verified Mattermost passthrough bridge still auto-submits correctly

### Current State
- Subscribe → `/dose/login/` with pre-filled credentials (user clicks submit manually)
- After Django login → credentials restored to session via API
- Click Mattermost → passthrough bridge auto-submits → redirects to `/channels/town-square`
- Team is NEVER specified during login; Mattermost handles team selection post-auth

### Next Session (Office)
1. Test subscribe → login → Mattermost flow end-to-end
2. Address Mattermost spinner issue if still present
3. Restart Mattermost server for plugin uploads
4. Deploy plugin to Mattermost server

---

## 2026-05-27 (Evening — Office) — Login After Subscribe Fix ✅

**Status**: ✅ COMPLETE — subscribe flow now redirects to custom login view that sets search_path TO public
**Branch**: main

### Problem
After subscribing, new users were redirected to `/accounts/login/` (allauth) with pre-filled credentials. Submitting the form gave "invalid username or password" error. Same credentials worked on "normal login" (custom `/dose/login/` view).

### Root Cause
Allauth's login view does not explicitly set `search_path TO public` before calling `authenticate()`. In the multi-tenant setup, the database connection may be in a tenant schema context when allauth tries to authenticate, causing the user lookup to fail (users are created in the public schema).

The custom `login_view` in `main.py` explicitly sets `search_path TO public` before `authenticate()`, which is why "normal login" worked.

### Fix
1. **Added `/dose/login/` route** to `dose/urls.py` — maps to custom `login_view` that sets `search_path TO public`
2. **Changed subscribe redirect** from `/accounts/login/` to `/dose/login/` in `subscribe.html`
3. **Updated `dose/login.html`** with auto-submit logic and Mattermost credential restoration (matching `account/login.html` functionality)
4. **Updated `index()` redirect** to use `/dose/login/` instead of `/accounts/login/` for consistency

### Files Changed
- `dose/urls.py` — added `path('login/', login_view, name='login')`
- `dose/templates/dose/subscribe.html` — changed redirect URL to `/dose/login/?next=/admin/`
- `dose/templates/dose/login.html` — added auto-submit + Mattermost credential restoration + debug logging
- `dose/views/main.py` — changed `index()` redirect to `/dose/login/`

### Verification
- All Python files pass syntax check
- `/dose/login/` explicitly sets `search_path TO public` before `authenticate()`
- Auto-submit and credential restoration logic mirrors `account/login.html`

### Follow-ups
- Test subscribe → auto-login → Mattermost flow end-to-end
- Restart Mattermost server to enable plugin uploads
- Deploy plugin to Mattermost server

---

## 2026-05-27 (Evening — Office) — Mattermost Team Name Cleanup ✅

**Status**: ✅ COMPLETE — all team name references removed from login flow
**Branch**: main

### Summary
Continued cleanup from morning session. Removed all remaining team name retrieval and specification code from Mattermost passthrough handler. The login flow now never specifies a team — Mattermost handles team selection naturally after successful authentication, exactly like direct login.

### Key Fixes
1. **Removed `_get_team_name` method** — deleted entire method from `mattermost_handler.py` (dead code, no longer called anywhere)
2. **Removed team name retrieval from login bridge** — login bridge no longer fetches `mm_team_name` from credentials or extra config
3. **Removed `teamName` JavaScript variable** — login bridge template no longer injects team name into JS
4. **Removed `mm_team_name` from credential storage** — `subscription_views.py` no longer stores team name in `PassthroughCredentialContainer`

### Files Changed
- `dose/passthrough/handlers/mattermost_handler.py` — removed `_get_team_name` method, team retrieval from login bridge, `teamName` JS variable
- `dose/subscription_views.py` — removed `mm_team_name` from credential storage

### Verification
- Syntax check passes on all modified files
- No remaining references to `_get_team_name` or `team_name_js` in handler
- Team name is never specified during login; Mattermost determines it post-auth

### Follow-ups
- Test subscribe → auto-login → Mattermost flow end-to-end
- Restart Mattermost server to enable plugin uploads
- Deploy plugin to Mattermost server

---

## 2026-05-27 (Morning — Condo) — Mattermost Auto-Login After Subscribe Debug ✅

**Status**: ✅ COMPLETE — team specification removed from redirects, credentials preserved across login
**Branch**: main

### Summary
Debugged Mattermost auto-login failure after subscription. The issue was that team names were being explicitly specified in redirects when they shouldn't be - direct login works without team specification, so auto-login should mimic that behavior. Also fixed credential loss during Django login redirect by preserving Mattermost credentials in sessionStorage and restoring them after login.

### Key Fixes
1. **Root handler team specification removed** — `mattermost_handler.py` line 117 changed from `/{team}/channels/town-square` to `/channels/town-square`. Let Mattermost handle team selection naturally after authentication.
2. **Credential preservation across login** — Mattermost credentials (username, password, token) stored in sessionStorage during subscribe, restored via API after Django login. Django creates new session on login, so credentials stored in old session were lost.
3. **Subscription response payload** — Added Mattermost credentials to `_subscription_response_payload` so frontend can store them in sessionStorage.
4. **Login template auto-submit** — Added debug logging to trace auto-login flow and credential restoration.
5. **API endpoint for credential restoration** — Added `restore_mm_credentials` endpoint to restore credentials to Django session after login (without team name - team determined by Mattermost post-auth).

### Files Changed
- `dose/passthrough/handlers/mattermost_handler.py` — removed team from root redirect (line 117)
- `dose/templates/dose/subscribe.html` — store Mattermost credentials in sessionStorage (without team name)
- `dose/subscription_views.py` — add Mattermost credentials to response payload
- `dose/templates/account/login.html` — add credential restoration API call + debug logging
- `dose/views/main.py` — add `restore_mm_credentials` API endpoint
- `dose/views/__init__.py` — export `restore_mm_credentials`
- `dose/urls.py` — add route for `restore_mm_credentials`

### Verification
- User confirmed credentials are correct (otherwise would redirect to login page)
- Action path no longer includes team specification
- Normal login works fine
- Auto-login after subscribe now preserves credentials without specifying team

### Follow-ups
- Restart Mattermost server to enable plugin uploads
- Deploy plugin to Mattermost server
- Test UI with plugin diagnostics after deployment

---

## 2026-05-14 (Morning — Condo) — Cloud SQL Live ✅ + Secrets Uploaded to GCP ✅

**Status**: ✅ COMPLETE — Cloud SQL migrated, superuser created, all 37 secrets in Secret Manager  
**Branch**: `main`

### What Was Done
- Fixed `dosedbadmin` password in GCP Console (was set wrong at office — now `PolySaaS2026!`)
- Fixed condo `.env`: `DOSE_DB_PASSWORD=PolySaaS2026!`, `DB_HOST=8.230.100.97`, `DB_PORT=5432`
- Ran `python manage.py migrate` → **107 migrations applied clean to Cloud SQL** (public schema)
- Created Django superuser: `dosedbadmin@polysaas.online` on Cloud SQL (0 tenants — fresh start)
- Installed Google Cloud CLI to `F:\gcloud\Google\Cloud SDK\`
- Installed `google-cloud-secret-manager` into venv
- Created `upload_env_to_secret_manager.py` one-time utility script
- Authenticated via `gcloud auth application-default login`
- **Uploaded all 37 `.env` secrets to GCP Secret Manager** (`project=application-integration-4524`)

### Secrets Now in Secret Manager (all 37)
Key secrets include: `django-secret-key`, `dose-db-password`, `db-host`, `db-port`,
`stripe-*` keys, `xai-api-key`, `gemini-api-key`, `anthropic-api-key`,
`mattermost-admin-token`, `bot-token-supergrok`, `bot-token-gem`, `bot-token-cc`,
`ai-peers-webhook-token`, `mattermost-url`, `redis-url`, all Stripe price IDs.

### Next Steps (Office)
1. **Hook Django into Secret Manager** — replace `.env` reads with Secret Manager calls
   - Pattern: `secretmanager.SecretManagerServiceClient().access_secret_version(name=...)`
   - Or use `django-environ` + a startup loader that pulls from SM into `os.environ`
2. **Install Google Cloud CLI on office desktop** (`F:\gcloud` or `C:\gcloud`)
   - Run `gcloud auth application-default login`
   - Run `python upload_env_to_secret_manager.py --dry-run` to verify (then skip — already uploaded)
3. **Lock down Cloud SQL IP whitelist** — GCP Console → Cloud SQL → Authorized Networks
   - Replace `0.0.0.0/0` with office IP `/32` + condo IP `142.111.152.39/32`
4. **Install and test Cloud Pub/Sub**
   - `pip install google-cloud-pubsub`
   - Create topic + subscription in GCP Console
   - Write a small test publisher/subscriber
5. **Fix Mattermost bot listener token** — add to `.env`:
   ```
   MATTERMOST_BOT_TOKEN=tfbzbw69pjg33cedaegg99hqch
   ```
   Then: `python manage.py run_mattermost_bot`

### Cloud SQL Reference
| Item | Value |
|------|-------|
| Project | `application-integration-4524` |
| Instance | `free-trial-first-project` |
| Public IP | `8.230.100.97:5432` |
| DB | `dosedbsaas` |
| User | `dosedbadmin` |
| Password | `PolySaaS2026!` |

---

## 2026-05-13 (Evening — Office) — Cloud SQL Connected ✅ Restore In Progress

**Status**: ⚠️ IN PROGRESS — Cloud SQL live, pg_dump running, restore pending  
**Branch**: `main`

### What Was Done
- GCP Project: `application-integration-4524`
- Cloud SQL instance: `free-trial-first-project` (PostgreSQL 18, us-south1)
- Connection name: `application-integration-4524:us-south1:free-trial-first-project`
- Public IP: `8.230.100.97`, Port: `5432`
- DB: `dosedbsaas`, User: `dosedbadmin`, Password: `PolySaaS2026!`
- `settings.py` updated — DB connection fully env-var driven (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`)
- Added to `.env`: `DB_HOST=8.230.100.97`, `DB_PORT=5432`
- Authorized networks: `0.0.0.0/0` (temporary — lock down after restore)
- `python manage.py migrate` ran clean → public schema + olient migrated OK
- **pg_dump from local `localhost:5433` in progress via pgAdmin** (Custom format, file: `dosedbsaas_backup.dump`)

### Next Steps (Morning)
1. **Restore the dump to Cloud SQL** — pgAdmin → Cloud SQL server (`8.230.100.97:5432`) → right-click `dosedbsaas` → Restore → select `dosedbsaas_backup.dump`
2. Test app against Cloud SQL: `python manage.py runserver`
3. Fix Mattermost bot listener token: add `MATTERMOST_BOT_TOKEN=tfbzbw69pjg33cedaegg99hqch` to `.env`
4. Lock down Cloud SQL IP whitelist — replace `0.0.0.0/0` with `142.111.152.39/32`
5. Add API keys to `.env` for CC bot: `ANTHROPIC_API_KEY=<key>`

---

## 2026-05-13 (Morning — Condo, Session 2) — AI Peers Bot Build ⚠️ Needs Token Fix

**Status**: ⚠️ IN PROGRESS — bot built, connects to correct URL, blocked on invalid listener token  
**Branch**: `main`

### What Was Built
- Full 5-peer AI roster: `@grok` (supergrok/xAI), `@gemini` (gem/Google), `@cc` (Cursor Claude/Anthropic), `@wsc` (Windsurf Claude), `@kimi` (Moonshot)
- `dose/mattermost_bot/routers/` package: `grok_router.py`, `gemini_router.py`, `cc_router.py`, `wsc_router.py`, `kimi_router.py`
- `bot.py` rewritten: peer table, real bot token posting (each peer posts under its own MM account), `@anyone` = all active peers, echo protection, urlparse URL fix
- `mysite/settings.py`: all bot tokens + API keys added (`BOT_TOKEN_SUPERGROK`, `BOT_TOKEN_GEM`, `BOT_TOKEN_CC`, `BOT_TOKEN_WSC`, `BOT_TOKEN_KIMI`, `XAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `KIMI_API_KEY`)
- Shela's system prompt incorporated into grok_router.py

### Keys in .env (already set)
- `XAI_API_KEY` ✅
- `GEMINI_API_KEY` ✅
- `MATTERMOST_URL=https://polysaas-mattermost.onrender.com` ✅
- `BOT_TOKEN_SUPERGROK`, `BOT_TOKEN_GEM`, `BOT_TOKEN_CC` ✅

### Blocker — Listener Token Expired
- `MATTERMOST_ADMIN_TOKEN=h4wd46ha8fbc7kdanzsi1w8zye` → "Invalid or expired session"
- **Fix at office — add this line to `.env`:**
  ```
  MATTERMOST_BOT_TOKEN=tfbzbw69pjg33cedaegg99hqch
  ```
  (This is the `condotest` PAT — already created, still valid)
- Once added, run:
  ```
  git pull
  .\venv\scripts\activate
  python manage.py run_mattermost_bot
  ```
- Test with: post `@grok what is PolySaaS?` in Town Square — supergrok should reply

### Next Steps
1. Fix listener token in .env at office
2. Test bot end-to-end (grok + gemini)
3. Add `ANTHROPIC_API_KEY` to .env for CC/WSC
4. `polysaasot` tenant PAT still pending

---

## 2026-05-13 (Morning — Condo) — Mattermost SSO + WebSocket BINGO ✅

**Status**: ✅ COMPLETE — merged to `main`  
**Branch**: `fix/mattermost-sso-restore` → `main`

### What Was Fixed
- Straight in, no login form, no loop, full channels view renders, no WebSocket banner
- Root cause 1: `mattermost_handler.py` had auto-submit disabled + false-positive bounce detector from debug session
- Root cause 2: WebSocket shim was routing `wss://` through the WSGI proxy (can't handle upgrades) — fixed to go direct to Mattermost server
- Root cause 3: `passthrough_embed.html` had 129 lines of CSS containment rules that hid the channel view
- Render env vars: `MM_SERVICESETTINGS_WEBSOCKETURL`, `ALLOWCORSFROM`, `CORSALLOWCREDENTIALS` added

### Files Changed
- `dose/passthrough/handlers/mattermost_handler.py` — restored + WebSocket shim fixed
- `dose/templates/admin/passthrough_embed.html` — restored from checkpoint
- `render.yaml` — WebSocket + CORS env vars
- `documentation/BINGO_MATTERMOST_SSO_WEBSOCKET.md` — full BINGO doc

### Next Steps
1. Store PAT for `polysaasot` tenant in TenantApp extra_config (token: `condotest`)
2. Nextcloud SSO

---

## 2026-05-12 (Evening — Office) — SSO Debug + Branch Preservation

**Status**: ⚠️ IN PROGRESS — broken main preserved, working version branched off  
**Branch**: `fix/mattermost-sso-restore` (use this), `checkpoint/2026-05-12-working` (frozen safe copy)

### What Happened
- `origin/main` was broken by debug changes during the day session:
  - Auto-submit commented out in login bridge
  - False-positive bounce detector blocked login
  - Aggressive token clearing caused loop
- Working version from this morning (commit `6664558`) preserved as `checkpoint/2026-05-12-working`
- `fix/mattermost-sso-restore` branch created: `origin/main` + restored `mattermost_handler.py` from checkpoint

### Pending Issues for Next Session
1. **`polysaastmon` tenant (t20)** — Mattermost env var changes during the day may have broken provisioning; `polyt20@polysaas.online` shows no valid session
2. **`fix/mattermost-sso-restore`** needs testing — if SSO works, merge to `main`
3. **`main` is still broken** — do not deploy main until fix branch is verified

### Next Session First Task
1. Test `fix/mattermost-sso-restore` branch — confirm Town Square loads for `polysaast4`
2. If working → merge to main, delete fix branch
3. Investigate `polysaastmon` Mattermost provisioning (check env vars on Mattermost service)

---

## 2026-05-11 (Morning — Office) — Mattermost SSO Verified Working ✅

**Status**: ✅ COMPLETE  
**Branch**: main  
**Location**: Office  
**Session Change**: Desktop → Laptop

### Current State (What's Working NOW)
| Component | Status | Notes |
|-----------|--------|-------|
| Mattermost Server-Side SSO | ✅ WORKING | No form displayed, straight to Town Square |
| Odoo SSO | ✅ WORKING | Auto-login, apps page loads |
| Orchestration Pipeline | ✅ WORKING | Invoice → Mattermost notification |
| Login Bridge (fallback) | ⚠️ DISABLED | Auto-submit commented out; not needed |

### How Mattermost SSO Works (Current)
1. User clicks Mattermost in sidebar
2. `try_root_display_shell_response` detects no `MMAUTHTOKEN` cookie
3. `get_upstream_cookies()` → POST to Mattermost API with credentials from `TenantApp.extra_config`
4. Sets `MMAUTHTOKEN` cookie, redirects to `/channels/town-square`
5. Mattermost SPA loads with valid session

**Credentials** (in `polysaast4` TenantApp `extra_config`):
- `mattermost_login_id` = `odooAdmin`
- `mattermost_password` = `PolySaaS2026!`

### Files Changed This Session
- `dose/passthrough/handlers/MATTERMOST_SSO_PROGRESS.md` — Updated to reflect working state

### Next Steps for Next AI/User
| Priority | Task | Notes |
|----------|------|-------|
| 1 | Nextcloud SSO | Apply same server-side SSO pattern |
| 2 | (Optional) Re-enable bridge auto-submit | Uncomment lines 206-211 in `mattermost_handler.py` |
| 3 | (Optional) Remove bridge entirely | If server-side SSO stays reliable |

### Committed This Session
- ✅ Documentation updated to reflect actual working state

### Pending / Not Committed
- None

---

## 2026-05-04 — The "Stupid Debug Session" (Paradigm Shift)

**Status**: Debugging in progress  
**Branch**: main  
**Time**: ~6 hours of cloud-deploy-debug iterations before realizing local dev is the only sane approach

### Summary
Spent 6+ hours debugging Odoo passthrough blank screen issue using the **insane** methodology: edit code → commit → push → wait for Render deploy → check gimpy logs → repeat. This is the **wrong way** to debug. Both user and assistant failed to recognize this immediately.

The actual working approach: **Develop and test locally first**, then deploy once it's working. User has full local setup (Postgres, Docker apps) but wasn't using it for passthrough debugging.

### Key Issues Discovered

**1. Template Missing Bug**
- `_wrap_in_admin_template()` in `middleware.py` tried to render `admin/passthrough_embed.html` which **did not exist**
- Created `templates/admin/passthrough_embed.html` to fix

**2. Odoo Auto-Init Bug**
- Entrypoint script checked if `ir_module_module` **table existed**, not if `web` module was **installed**
- Database had empty tables from failed init → `web.login` template not found → 500 errors
- Fixed entrypoint to check `SELECT state FROM ir_module_module WHERE name = 'web'`

**3. Handler Returns None for /web/login**
- `try_root_display_shell_response` returns `None` for non-root paths
- Falls through to forwarder, which wraps raw Odoo response
- This is actually working as designed (handler only handles root path redirect)

**4. 502 Error Handling**
- Added better error display when upstream service returns 502/503/504 instead of blank page

### Root Cause of Blank Page
The blank page persists despite fixes. Current theory:
1. Handler returns `None` for `/web/login` → falls through to forwarder
2. Forwarder gets 200 OK from Odoo with valid HTML
3. `_is_initial_page_load()` may be returning `False` for some reason (treating HTML as API/asset)
4. OR the wrapped template is rendering empty content

**Next Step**: Test locally with full debug output to see exactly what `_is_initial_page_load` decides and what the wrapped HTML looks like.

### Files Changed Today
1. `templates/admin/passthrough_embed.html` — CREATED (missing template)
2. `deploy/odoo-render/entrypoint-render.sh` — FIXED (check web module state, not just table existence)
3. `dose/passthrough/middleware.py` — ADDED error handling for 502/503/504

### Paradigm Shift
**OLD (stupid) workflow:**
- Edit → Commit → Push → Wait 2-5 min for deploy → Check gimpy Render logs → Repeat
- 6+ hours, no resolution

**NEW (correct) workflow:**
- Run Core locally on localhost:8000
- Test passthrough pointing to Render Odoo (or local Docker Odoo)
- Full console logs, instant turnaround, can use debugger
- When working, commit → push → quick Render verification

### Next Session (2026-05-05)
**User will:**
1. Set `DOSE_DB_PASSWORD` in `.env` for local Postgres
2. Run `python manage.py runserver`
3. Access `http://localhost:8000/admin/`
4. Click Odoo passthrough link
5. Check full debug output in console

**Or:** Test via URL directly: `http://localhost:8000/pt/admin/polysaas-odoo2.onrender.com/web/login`

**Assistant will:**
- Help interpret local debug output
- Fix whatever `_is_initial_page_load` or wrapper issue is causing blank page
- Once working locally, commit and push to Render

---

## 2026-04-29
**Status**: In Progress
**Branch**: main

### Summary
Explored existing passthrough infrastructure and implemented permanent passthrough infrastructure for Odoo and Mattermost. This is production infrastructure, not a one-off demo - users subscribe and have instant access to the apps they subscribed to. Confirmed both Odoo and Mattermost passthrough handlers already exist and are PolySniffer-generated for dynamic event capture during passthrough sessions.

### Key Findings
- **PassthroughAuthMiddleware**: Injects auth headers/JWT on `/pt/` paths with tenant info (tenant_slug, tenant_name)
- **OdooPassthroughHandler**: Comprehensive handler with display shell, auto-login via JSON-RPC, path rewriting, WebSocket support
- **MattermostPassthroughHandler**: Comprehensive handler with display shell, auto-login via MMAUTHTOKEN, WebSocket/fetch/XHR patching
- **Handler Registry**: Both handlers registered with trigger_path matching
- **PassThroughEndpoint model**: Stores endpoint configuration (trigger_path, endpoint_url, menu integration)
- **TenantApp model**: Tracks which apps are provisioned per tenant (odoo, mattermost, nextcloud, etc.)
- **Subscription flow**: Automatically creates TenantApp records when users select apps during subscription
- **Tenant provisioners**: Both odoo_tenant_provisioner.py and mattermost_tenant_provisioner.py exist and are wired to subscription

### Files Reviewed
- `dose/middleware/passthrough_auth.py` - Auth injection middleware
- `dose/models/tenant_app.py` - Tenant app tracking model
- `dose/passthrough/handlers/odoo_handler.py` - Odoo passthrough handler (PolySniffer-generated)
- `dose/passthrough/handlers/mattermost_handler.py` - Mattermost passthrough handler (PolySniffer-generated)
- `dose/models/pass_through_endpoint.py` - Endpoint configuration model
- `dose/context_processors.py` - Navigation context processor
- `dose/passthrough/middleware.py` - Main passthrough middleware
- `dose/passthrough/handlers/registry.py` - Handler registry
- `dose/services/odoo_tenant_provisioner.py` - Odoo provisioning service
- `dose/services/mattermost_tenant_provisioner.py` - Mattermost provisioning service
- `dose/management/commands/setup_default_passthrough_endpoints.py` - Production setup command for default endpoints
- `dose/subscription_views.py` - Subscription flow with provisioner wiring

### Changes Made
- Added `starting_uri` field to PassThroughEndpoint model (migration 0043)
- Fixed TenantApp tenant_id column type from bigint to varchar (migration 0044)
- Created PassThroughEndpoint records for Odoo (http://localhost:8069) and Mattermost (http://localhost:8065)
- Created management command `setup_default_passthrough_endpoints` for production endpoint setup
- Renamed from demo-focused naming to production-focused naming

### Files Changed
- `dose/models/pass_through_endpoint.py` - Added starting_uri field
- `dose/migrations/0043_passthroughendpoint_starting_uri.py` - Migration for starting_uri field
- `dose/migrations/0044_alter_tenantapp_tenant_id_to_varchar.py` - Migration for tenant_id type fix
- `dose/management/commands/setup_default_passthrough_endpoints.py` - Production endpoint setup command

### Follow-ups
1. Ensure Odoo and Mattermost services running at configured URLs
2. Test subscription flow with enable_odoo and enable_mattermost
3. Verify Odoo passthrough auto-login and navigation
4. Verify callback data capture for Odoo events
5. Verify Mattermost team creation with tenant slug
6. Verify Mattermost passthrough and town square posting
7. Wire PolySniffer to capture Mattermost chat events for AI adapter triggering
8. Implement AI Adapter using Windsurf API
9. Implement AI Adapter using Grok API
10. Wire passthrough dynamic event handling for 3-way AI conversation (Windsurf + Grok + human/Mattermost)

---

## 2026-04-29 (Session End)
**Status**: Session Complete
**Branch**: main

### Summary
Implemented permanent passthrough infrastructure for Odoo and Mattermost. User clarified this is production behavior (not one-off demo) - users subscribe and have instant access to apps they selected. All infrastructure is now permanent and committed to GitHub.

### Files Changed
- `dose/models/pass_through_endpoint.py` - Added starting_uri field
- `dose/migrations/0043_passthroughendpoint_starting_uri.py` - Migration for starting_uri field
- `dose/migrations/0044_alter_tenantapp_tenant_id_to_varchar.py` - Migration for tenant_id type fix
- `dose/management/commands/setup_default_passthrough_endpoints.py` - Production endpoint setup command (renamed from demo)
- `documentation/COORDINATION_README.md` - Updated coordination log

### Commits
- 95b3b4c: Add permanent passthrough infrastructure for Odoo and Mattermost
- 31a2894: Update coordination log with production passthrough infrastructure changes

---

## 2026-05-01
**Status**: ✅ COMPLETE - BINGO!
**Branch**: main

### Summary
Fixed blank Django admin user edit page on production (Render). The issue was caused by a multi-tenancy schema mismatch where UserProfile objects were in tenant schemas but trying to reference User objects in public schema. When the inline form tried to render, it crashed because the related User wasn't accessible in the tenant schema context.

### Key Fixes
- Fixed `CustomUserAdmin.get_object()` to force `search_path TO public` before querying users
- Added `get_queryset` to `UserProfileInline` to query from public schema and filter inaccessible profiles
- Fixed `UserProfile.__str__` to handle `User.DoesNotExist` gracefully
- Fixed template block inheritance in `base_site.html`

### Files Changed
- `dose/admin.py` - Schema-aware User and UserProfile query handling
- `dose/models/user_profile.py` - Graceful handling of missing user in __str__
- `dose/templates/admin/base_site.html` - Fixed Jazzmin block inheritance
- `dose/tenant_utils.py` - Added tenant debugging logging
- `dose/management/commands/migrate_users_to_public.py` - User migration command
- `dose/management/commands/check_template_loading.py` - Template diagnostics

### Verification
- ✅ User list page loads correctly
- ✅ User edit form displays with all fields
- ✅ Can save changes to users
- ✅ No more `DoesNotExist` errors

### Follow-ups
- Consider moving UserProfile table to public schema for consistency
- Ensure future user creation always happens in public schema
- Document this multi-tenancy pattern to prevent regression

### Commits
- See `documentation/BINGO_Blank_Admin_User_Edit_Fix.md` for full details

---

## 2026-05-01 (Morning Session)
**Status**: In Progress
**Branch**: main

### Summary
Fixed passthrough endpoint visibility and functionality for the current tenant. The passthrough endpoints (Odoo, Mattermost, NextCloud) are now correctly displayed in the Django admin sidebar and functional. Fixed middleware and views to properly query `PassThroughEndpoint` records within tenant schemas by setting `search_path` before database queries.

### Key Fixes
- Modified `setup_default_passthrough_endpoints` command to support tenant schemas with `--tenant-slug` argument
- Added NextCloud endpoint creation to the setup command
- Updated Odoo, Mattermost, NextCloud provisioners to create `PassThroughEndpoint` records in tenant schemas on subscription
- Fixed `admin_views.py` `passthrough_embed_view` to set tenant schema `search_path` before querying endpoints
- Fixed `passthrough/middleware.py` `run_pt_admin_passthrough_core` to set tenant schema `search_path` before querying endpoints
- Changed `URLField` to `CharField` for `endpoint_url` and `api_endpoint` in `PassThroughEndpoint` model to allow internal Docker hostnames
- Added fallback and debug logging to Odoo handler for when HTML body tag extraction fails

### Files Changed
- `dose/management/commands/setup_default_passthrough_endpoints.py` - Added tenant slug argument, NextCloud endpoint, schema-aware creation
- `dose/services/odoo_tenant_provisioner.py` - Added PassThroughEndpoint creation in tenant schema
- `dose/services/mattermost_tenant_provisioner.py` - Added PassThroughEndpoint creation in tenant schema
- `dose/services/nextcloud_tenant_provisioner.py` - Added PassThroughEndpoint creation in tenant schema
- `dose/admin_views.py` - Fixed passthrough view to set tenant schema search_path
- `dose/passthrough/middleware.py` - Fixed middleware to set tenant schema search_path
- `dose/models/pass_through_endpoint.py` - Changed URLField to CharField for Docker hostname support
- `dose/passthrough/handlers/odoo_handler.py` - Added fallback and debug logging for body extraction

### URLs Configured
- Odoo: `https://polysaas-odoo2.onrender.com`
- Mattermost: `https://polysaas-mattermost.onrender.com`
- NextCloud: `http://polysaas-nextcloud:80` (internal Docker)

---

## 2026-05-02 (Morning Session)
**Status**: In Progress
**Branch**: main

### Summary
Extended passthrough infrastructure to all 6 bundled apps (Odoo, Mattermost, NextCloud, Dolibarr, Liferay, WordPress). Created AI WebChat Bridge architecture plan with Sheila's review feedback, and implemented Mattermost Bot skeleton with Kimi + Claude adapters.

### Key Changes
- Extended `setup_default_passthrough_endpoints` command to support all 6 bundled apps
- Fixed `dolibarr_tenant_provisioner.py`, created `liferay_tenant_provisioner.py` and `wordpress_tenant_provisioner.py`
- Created comprehensive AI WebChat Bridge Plan (`documentation/AI_WebChat_Bridge_Plan.md`) — Sheila reviewed
- Implemented `dose/ai_bridge/` package (base, kimi, claude adapters + mattermost bot)

### Status
- ✅ All 6 bundled app provisioners committed and pushed
- ✅ AI WebChat Bridge Plan committed (Sheila reviewed)
- ✅ Kimi + Claude adapters + Mattermost Bot committed
- ⚠️ Odoo passthrough blank — root cause was DB gone (app on cache), NOT code bugs

---

## 2026-05-03 (Early Morning — Laptop)
**Status**: ✅ BINGO
**Branch**: main

### Summary
Fixed Odoo passthrough blank/garbled screen. Odoo login form now renders correctly inside PolySaaS admin shell.

### Root Cause Chain
1. Sidebar URL used `trigger_path` norm instead of `endpoint_url` hostname → middleware lookup always missed
2. No root redirect for hostname triggers → browser hit Odoo `/` returning garbled bytes
3. `brotlicffi` missing from requirements.txt → Render CDN's Brotli-encoded responses decoded as garbled UTF-8
4. `allow_redirects=False` caused 502 on Render → reverted to True
5. **KEY INSIGHT**: Many apparent "code bugs" in previous sessions were actually caused by `polysaas_postgres` DB being gone — app was running on cached session data

### Key Architecture Rule
- Sidebar href = `/pt/admin/<endpoint_url hostname>/`
- Middleware matches endpoint by `endpoint_url__icontains="://<hostname>"` (DB lookup)
- Root path → Django redirect to `/web/login` (browser URL stays correct)
- `allow_redirects=True` for GET, `False` for POST (browser follows post-login redirect to correct URL)
- `brotlicffi==1.1.0.0` in requirements.txt for Brotli decompression

### Files Changed
- `dose/context_processors.py` — sidebar URL from `endpoint_url` hostname
- `dose/passthrough/middleware.py` — endpoint lookup by `endpoint_url` hostname
- `dose/passthrough/handlers/odoo_handler.py` — root redirect to `/web/login`, smarter allow_redirects
- `requirements.txt` — added `brotlicffi==1.1.0.0`
- `documentation/BINGO_Odoo_Passthrough_Login.md` — this session's BINGO doc

### Rollback Note
Rolled back 47 commits to `0616583` (last BINGO). All discarded work saved on `passthrough-wip` branch on GitHub.

### Follow-ups for Next Session
- Test Odoo **post-login** (form submit → session → `/odoo/` apps page)
- Verify Location header rewriting works for post-login redirect
- Test Mattermost passthrough (same hostname approach)
- Re-integrate AI Bridge (Kimi/Claude adapters) from `passthrough-wip` branch
- Re-integrate provisioners for all 6 bundled apps from `passthrough-wip` branch

---

## 2026-05-03 — Odoo DB Disaster Recovery + Infrastructure Hardening

### Status: ✅ BINGO — Odoo healthy, service recovered 7:40 PM

### Branch: main

### Summary
Attempted to reset Odoo admin credentials via Odoo DB manager → the "Delete Database"
operation succeeded (despite showing a 500 error), wiping `polysaas_postgres` which was
shared by BOTH Django (Core) and Odoo. Both services went down.

Recovery steps taken:
- Created `polysaas_postgres` database in PgAdmin (reconnected to Render PostgreSQL)
- PolySaaS-Core redeployment still failing — DATABASE_URL may point to a DIFFERENT
  Render PostgreSQL than where the DB was recreated. Need to verify `DATABASE_URL` host.
- Set `PolySaaS-Odoo2 autoDeployTrigger: off` in render.yaml to prevent Python commits
  from triggering unnecessary Odoo redeployments.
- Identified root cause of shared DB: individual env vars on Odoo2 overrode group
  `ODOO_DB_NAME: odoodb` with `polysaas_postgres` (Django's DB name).

### Files Changed
- `render.yaml` — `PolySaaS-Odoo2 autoDeployTrigger: off`

### CRITICAL Next-Session Actions (do these FIRST)
1. Check `DATABASE_URL` in Render → PolySaaS-Core → Environment — get the DB hostname
2. Connect PgAdmin to THAT specific PostgreSQL host and create `polysaas_postgres` there
3. Manual Deploy PolySaaS-Core — wait for pre-deploy (migrate_all_schemas) to succeed
4. In Render → `polysaas-odoo` env group, set:
   - `ODOO_DB_HOST` = `dpg-d7lple0ebus73e3le4ug-a`
   - `ODOO_DB_USER` = `polysaas_postgres_user`
   - `ODOO_DB_NAME` = `odoodb` (NOT polysaas_postgres — keep them separate!)
   - `ODOO_DB_PASSWORD` = `yTfbrzBFpCpSfLCICemNZUbqnfq1G5yU`
5. Create `odoodb` database in PgAdmin: `CREATE DATABASE odoodb OWNER polysaas_postgres_user;`
6. Remove individual Odoo2 env overrides: `ODOO_DB_NAME`, `ODOO_DB_USER`, `HOST`
   (group values will take over cleanly)
7. Manual Deploy PolySaaS-Odoo2
8. Go to Odoo DB manager, create database with known admin password
9. Test Odoo login via passthrough — verify post-login redirect to apps page

---

## 2026-05-04 (Early Morning — Laptop → Office)
**Status**: IN PROGRESS — env group fixed, deploy pending
**Branch**: main

### Summary
Picked up at office. Odoo was in crash loop due to stale env group values. Fixed `polysaas-odoo` 
environment group to use correct Render PostgreSQL credentials and point to `odoo_prod` DB.

### Actions Completed
- Identified `polysaas-odoo` group had wrong values: `odoodb` (non-existent), `odoouser`, missing host/password
- Updated group values:
  - `DB_NAME` / `ODOO_DB_NAME`: `odoo_prod`
  - `ODOO_DB_USER`: `polysaas_postgres_user`
  - `ODOO_DB_HOST`: `dpg-d7lple0ebus73e3le4ug-a`
  - `ODOO_DB_PASSWORD`: `yTfbrzBFpCpSfLCICemNZUbqnfq1G5yU`
- Committed `render.yaml` changes:
  - Hardcoded `ODOO_DB_NAME=odoo_prod` on service (overrides group if needed)
  - Added `ODOO_AUTO_INIT=1` to force re-initialization (fixes missing `web.login` template)

### Pending (Next Session at Office)
- Wait for PolySaaS-Odoo2 Manual Deploy to complete init
- Verify `/web/login` renders without 500
- Reset admin password via SQL or DB manager
- Test passthrough login end-to-end
- **Remove `ODOO_AUTO_INIT`** from render.yaml after successful init

### Files Changed
- `render.yaml` — hardcoded `ODOO_DB_NAME` and `ODOO_AUTO_INIT` for Odoo2 service

---

## 2026-05-04 (Evening — Condo)
**Status**: PAUSED — 15hr day, new SDLC plan for tomorrow
**Branch**: main

### Summary
Odoo2 still not showing login via passthrough (blank screen on sidebar click). After frustrating 
debug cycle with Render logs, realized current SDLC is backwards: committing infra changes and 
waiting for Render deploy to test passthrough logic is painfully slow.

### New SDLC Rule (Effective Tomorrow)
1. **Develop and test passthrough logic LOCALLY first** — add logging, find errors, fix immediately
2. **Only commit/push to Render after local validation** — minimize Render cycle to final verification
3. **Local Django + local Postgres** for all passthrough development
4. **External services (Odoo, Mattermost, etc.) stay on Render** — accessed via passthrough as designed

### Tomorrow's First Task
Test Odoo passthrough locally:
- `python manage.py runserver`
- Click Odoo sidebar
- Add tracing to `odoo_handler.py` to find blank screen root cause
- Fix locally, verify, then commit/push

### Current Render Status
- PolySaaS-Odoo2: Running but passthrough shows blank (not 500)
- Env group values correct (`odoo_prod`, proper credentials)
- `ODOO_AUTO_INIT` still in YAML (remove after login works)

---

## 2026-05-05 (Evening — Condo)
**Status**: IN PROGRESS — Odoo login working, Mattermost admin lost
**Branch**: main

### Summary
Pulled from GitHub (38 objects from desktop session). Big news: **Odoo passthrough login is working** — apps screen renders after login. The earlier blank screen issue is resolved.

Mattermost admin credentials lost (thought they were `mmadmin` / `PolySaaS2026!` but not working). Recovery options identified:
- `mmctl user list` / `mmctl user change-password` in Render Shell
- `mattermost user create --local --system_admin` in Render Shell  
- Direct SQL on `mattermost` DB in PgAdmin as fallback

### Ultimate Goal (The North Star)
New subscriber → provision apps (Odoo, Mattermost, NextCloud, etc.) → SSO to those apps in the company's name seamlessly.

### Tomorrow's First Task
Recover Mattermost admin credentials, verify Mattermost passthrough login works end-to-end.

---

## 2026-05-06 (Morning — Condo → Office)
**Status**: DONE — Mattermost passthrough working
**Branch**: main

### Summary
Created Django superuser `mmadmin@polysaas.online` / `PolySaaS2026!` for local admin access.

**Mattermost passthrough is LIVE**: Clicking "Mattermost" in the PolySaaS admin sidebar loads the full Mattermost UI inside the passthrough proxy. User can log in with `mikeoliveraz` / `PolySaaS2026!` and sees Town Square, channels, direct messages. The shim correctly rewrites static assets (`/pt/admin/mattermost/static/...`) and API calls.

**Known cosmetic issues (non-blocking):**
- WebSocket banner "Mattermost unreachable" — Render free tier doesn't support WS upgrade; Mattermost falls back to HTTP polling automatically
- Plugin bundles (github, playbooks, nps, calls) return 404 — non-critical, core chat works
- External telemetry CORS errors (`pdat.matterlytics.com`) — unrelated to passthrough

**Pending for future sessions:**
- Auto-login via `MMAUTHTOKEN` injection (requires tenant app `extra_config` with Mattermost credentials)
- Fix plugin static asset routing through proxy
- WebSocket passthrough support (if Render plan supports it)

### Files Changed
- `documentation/COORDINATION_README.md` (this entry)

---

## 2026-05-07 / 2026-05-08 — Odoo Admin Credentials Recovery
**Status**: ✅ BINGO — `odooAdmin` / `PolySaaS2026!` working
**Branch**: main

### Summary
Odoo admin credentials were unknown (fresh Render deploy, default `admin` login set during DB wizard). Needed to establish known credentials `odooAdmin` / `PolySaaS2026!` for use across the team.

### Recovery Sequence

1. **Identified DB name confusion** — `ODOO_DB_NAME=odoo_prod` in env but actual DB used by Odoo was `odoodb` (set via Render env group). Confirmed via `printenv` in Render shell.

2. **Dropped `odoo_prod`** (empty/stale DB from previous failed init):
   ```bash
   # First terminated active connections:
   PGPASSWORD=... psql -h dpg-d7g2ombeo5us73aln4ug-a -U polysaas_postgres_user -d postgres \
     -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='odoo_prod';"
   # Then dropped:
   PGPASSWORD=... psql ... -c "DROP DATABASE odoo_prod;"
   ```

---

## 2026-05-16 (Morning — Condo → Office) — Mattermost Login Loop Debug (INCOMPLETE)

**Status**: ⚠️ IN PROGRESS — spinner still not ending, issue not resolved  
**Branch**: main  
**Location**: Condo → Office (handoff)

### Summary
Debugging Mattermost login loop and persistent spinner issue. The login bridge is working (credentials auto-filled, login succeeds), but after redirect to Town Square, the spinner never ends and the user gets stuck in a loop.

### What Was Attempted
1. **Removed upstream validation** from fetch/XHR interceptors — CORS blocks cross-origin requests to Mattermost server from localhost:8000
2. **Fixed login bridge** to only treat non-empty tokens (length > 10) as valid — prevents empty strings from triggering auto-redirect
3. **Verified middleware** correctly intercepts `/?extra=expired` redirects and redirects to login bridge
4. **Confirmed static assets** loading correctly (no 404s after previous fixes)

### Current State
- Login bridge loads with credentials auto-filled
- Login succeeds (token obtained)
- Redirect to Town Square happens
- **Spinner never ends** — Mattermost client stuck in loading state
- Token appears to be empty in localStorage (`localStorage.setItem("MMAUTHTOKEN") = ""`)

### Root Cause Suspected
The token is being set to an empty string after login, which causes the Mattermost client to fail authentication and get stuck in a spinner loop. The login bridge's `_bridge_login` endpoint may not be setting the cookie correctly, or the shim's token injection is not working.

### Files Changed
- `dose/passthrough/handlers/mattermost_handler.py` — removed upstream validation (lines 1078-1092, 1101-1110), fixed login bridge token validation (line 354)

### Next Steps (Office)
1. **Debug `_bridge_login` endpoint** — verify it's setting the MMAUTHTOKEN cookie correctly
2. **Check browser DevTools** — verify MMAUTHTOKEN cookie is present after login
3. **Add more logging** to shim's `_getToken()` function to see where empty token comes from
4. **Consider server-side token injection** — if client-side shim can't reliably read the cookie

### Session Notes
- Upstream validation approach failed due to CORS — Mattermost server doesn't allow cross-origin requests with credentials from localhost:8000
- Reverted to simple 401 handling: clear token and redirect to login bridge
- Login bridge now only auto-redirects if token is non-empty and has reasonable length (> 10 chars)
---

3. **Redeployed `polysaas-odoo2`** via Render Manual Deploy — `ODOO_AUTO_INIT=1` recreated `odoodb` fresh. DB setup wizard ran on first visit, admin created with email `odooAdmin@polysaas.online` / `PolySaaS2026!`.

4. **Login failed** — discovered actual login stored was `admin` (Odoo default), not `odooAdmin`. Renamed via SQL:
   ```bash
   PGPASSWORD=... psql ... -d odoodb \
     -c "UPDATE res_users SET login='odooAdmin' WHERE id=2;"
   ```

5. **Password still failing** — previous `write({'password': ...})` ORM attempts didn't persist. Checked hash format:
   ```sql
   SELECT substring(password,1,50) FROM res_users WHERE id=2;
   -- Result: $pbkdf2-sha512$600000$...
   ```
   Format is `passlib` `$pbkdf2-sha512$` (NOT Django's `pbkdf2_sha512$`).

6. **Generated correct hash and updated via SQL** in Odoo shell:
   ```python
   from passlib.hash import pbkdf2_sha512
   h = pbkdf2_sha512.using(rounds=600000).hash('PolySaaS2026!')
   env.cr.execute("UPDATE res_users SET password=%s WHERE id=2", [h])
   env.cr.commit()
   ```

7. **Login worked** — `odooAdmin` / `PolySaaS2026!` (**case-sensitive**).

### Key Lessons
- **Odoo 18 login is case-sensitive** — `odooadmin` ≠ `odooAdmin`
- **Odoo 18 password hash format**: `$pbkdf2-sha512$600000$<salt>$<hash>` (passlib format, NOT Django format)
- **ORM `write({'password': ...})` unreliable** in shell — use `passlib.hash.pbkdf2_sha512.using(rounds=600000).hash()` + direct SQL
- **`_set_password()` API changed in Odoo 18** — takes 0 positional args (not the password string)
- **Don't share Django and Odoo Postgres DBs** — keep them completely separate to avoid `DROP DATABASE` disasters
- **Auto-deploy disabled on Render** — manual deploys only to control costs

### Credentials Card
Added `AppCredential` model + admin registration + template tag so credentials are configurable in **Admin → Dose → App credentials** rather than hardcoded. Card hidden by default, revealed via inconspicuous footer `·` trigger. Case-sensitivity warning shown in card footer.

---

## 2026-05-08 (Morning — Condo → Office)
**Status**: DONE — dashboard fix + Odoo2 deploy recovered
**Branch**: main

### Summary
1. **Fixed Django admin NoReverseMatch**: Added missing `path('dashboard/', dashboard, name='dashboard')` to `dose/urls.py`. The `templates/jazzmin/admin/index.html` references `{% url 'dose:dashboard' %}` but the route was never registered. Committed and pushed.
2. **Odoo2 deploy fixed**: Previous deploy failed because `ODOO_DB_NAME=odoo_prod` but database `odoo_prod` never existed. Changed to `odoodb` in `render.yaml` (which matches the DB initialized earlier). Also updated directly in Render dashboard env vars and triggered manual deploy. Build and deploy succeeded; service is live.
3. **Auto-deploy remains OFF**: All Render services have `autoDeployTrigger: off`. Manual deploys required from dashboard.

### Login Credentials Note
- Default Odoo superuser after `-i base,web` init: `admin / admin` (not `odooAdmin / PolySaaS2026!`)
- `odooAdmin / PolySaaS2026!` is only created by the tenant provisioner when a user subscribes

### Files Changed
- `dose/urls.py` — added missing `dashboard` named route
- `render.yaml` — changed `ODOO_DB_NAME` from `odoo_prod` to `odoodb`
- `documentation/COORDINATION_README.md` (this entry)

---

## 2026-05-08 (Evening — Desktop Session)
**Status**: ✅ BINGO — sidebar + Odoo login fixed
**Branch**: main

### Summary
1. **Sidebar 75×75 logo cards**: Updated `custom_sidebar.html` with 2-column grid of 75×75 app logos (Odoo, Mattermost) with app name labels below. Gradient backgrounds per app.
2. **Odoo passthrough login fix**: The `get_request_body` method was using `parse_qs` + `urlencode` round-trip which corrupted the password (`PolySaaS2026!` → `Po;ySaaS2026!`). Fixed to preserve raw body bytes and only surgically replace the `csrf_token` field via regex.
3. **Orchestration scaffolding started**: Created `OdooInvoiceNotifierService` (posts invoice notifications to Mattermost) and `setup_odoo_invoice_orchestration` management command. Blocked by `dose_instruction.tenant_slug` bigint issue (same root cause as before).

### Files Changed
- `dose/templates/admin/includes/custom_sidebar.html` — 75×75 logo card grid
- `templates/jazzmin/admin/index.html` — matching CSS for dashboard injection
- `dose/passthrough/handlers/odoo_handler.py` — raw body passthrough fix
- `dose/services/odoo_invoice_notifier_service.py` — NEW: Mattermost invoice notifier
- `dose/services/endpoint_data_extractor.py` — in-process MQ fallback
- `dose/management/commands/setup_odoo_invoice_orchestration.py` — NEW: wiring command

### Pending
- Fix `dose_instruction.tenant_slug` bigint → varchar in polysaas schema
- Run `setup_odoo_invoice_orchestration` command
- Green toast notification in passthrough shell
- End-to-end test: Odoo invoice → Mattermost notification

---

## 2026-05-09 (Morning — Condo)
**Status**: IN PROGRESS — subscribe + demo testing, UI fixes applied
**Branch**: main

### Summary
Started testing the full subscribe → provision → passthrough → demo flow.

**Fixes applied today:**
1. **Subscribe page checkbox alignment**: Added `.app-checkbox-row` flexbox styling so checkboxes are vertically centered and left-aligned with text to the right.
2. **Odoo passthrough login prepopulation**: Added `get_upstream_credentials()` method and client-side JS shim code to auto-fill the Odoo login form with tenant credentials (login/password/db) when navigating through the passthrough proxy.
3. **Odoo apps page missing icons**: Broadened `_rewrite_path` in `odoo_handler.py` to proxy ALL root-relative paths (not just `/web/`, `/odoo/` prefixes). Previously paths like `/base/static/` (app icons) were being made absolute to upstream origin, which browsers can't reach through the proxy. Now all assets route correctly through `/pt/admin/<host>/...`.
4. **CSS url() rewrite broadened**: The `<style>` block URL rewriter now catches ALL `url(...)` paths, fixing background-image-based icons.

**Notes / Pending:**
- **75x75 logo size**: User reports a change was made yesterday (May 8) to set passthrough app logos to 75x75 with labels underneath. This change should be verified and committed if not already in repo.
- **"Activate Invoicing" error**: `psycopg2.InterfaceError: cursor already closed` — this is an Odoo internal error during module installation. Likely caused by long-running DB transactions being interrupted by Render free-tier limitations or proxy timeouts. Not a proxy bug; Odoo's module install needs a stable long-lived connection.

### Files Changed
- `dose/templates/dose/subscribe.html` — checkbox alignment fix
- `dose/passthrough/handlers/odoo_handler.py` — login prepopulation + icon path rewriting fix
- `documentation/COORDINATION_README.md` (this entry)

---

## 2026-05-09 (Evening — Condo)
**Status**: ✅ BINGO — Odoo SSO working, apps page loads after login
**Branch**: main
**Commit**: `b2396a7`

### Summary
Changed strategy from client-side JSON-RPC auto-login to **server-side SSO** where PolySaaS authenticates with Odoo via `/web/session/authenticate` and returns the `session_id` to the browser. This avoids credential exposure in client-side JS and bypasses OWL framework button-click issues.

### Problem Discovered & Fixed
- Browser JS shim called `/dose/api/odoo-sso/` but got **404**
- Root cause: `path('api/', include(router.urls))` in `dose/urls.py` (DRF DefaultRouter) swallows ALL `/api/*` paths. The `api/odoo-sso/` route was defined **after** the router, so it never matched.
- **Fix**: Moved `path('api/odoo-sso/', odoo_sso_api, ...)` **before** `path('api/', include(router.urls))` in `dose/urls.py`

### Files Changed
- `dose/urls.py` — moved `api/odoo-sso/` route before DRF router to prevent 404
- `dose/passthrough/handlers/odoo_handler.py` — added debug `alert()` calls to trace SSO flow in browser
- `dose/odoo_sso_api.py` — NEW: server-side JSON-RPC auth endpoint (already committed in previous session)

### Next Session First Task
1. **Restart local server** if needed (`python manage.py runserver`)
2. **Navigate to Odoo passthrough** (e.g. `http://localhost:8000/pt/admin/polysaas-odoo2.onrender.com/`)
3. **Watch for alert sequence**:
   - `[PolySaaS Odoo] Auto-login starting for: ...`
   - `[PolySaaS Odoo] Calling SSO endpoint...`
   - `[PolySaaS Odoo] SSO response status: 200`
   - `[PolySaaS Odoo] SSO data: ...`
4. If status is 200 and data contains `session_id`, the shim sets `document.cookie` and reloads the page
5. After reload, verify Odoo apps/dashboard loads (not blank)
6. **Remove debug alerts** from `odoo_handler.py` once flow is confirmed working

### If Still Blank After SSO
- Check browser DevTools Network tab for the reload request — does it send `session_id` cookie?
- Check server logs — does the reload hit `/pt/admin/.../web/` with the authenticated session?
- The `override_upstream_cookies` logic skips injecting tenant session if browser already has one
- Consider whether `SameSite=Lax` cookie needs `Secure` flag when running through Render HTTPS

### Credentials
- Tenant T13 login: `pst13@polysaas.online` / `PolySaaS2026!`
- DB: `odoodb`

---

## 2026-05-10 (Morning — Condo)
**Status**: IN PROGRESS — orchestration event mapping wired, awaiting first end-to-end test
**Branch**: main
**Commits**: `6ef8fcf`, `a8b7b69`

### Summary
Pulled last night's SSO BINGO changes. Applied migration 0047 (`match_type` + `match_extra` on `Instruction`) to all local schemas. Wired the full invoicing orchestration event mapping.

### Changes Made

**1. Migration 0047 applied locally**
- Adds `match_type` (path/action_id/menu_id/regex/contains) and `match_extra` (JSON AND conditions) to `Instruction` model

**2. `orchestration_hook.py` — query fix**
- Removed `tenant=tenant` FK filter (was causing `invalid input syntax for type bigint` error)
- Schema isolation is handled by `SET search_path TO tenant_schema, public` — no FK filter needed

**3. `orchestration_hook._instruction_matches` — AND conditions via `match_extra`**
- `{"menu_id": "116"}` — also require menu_id in URL (AND)
- `{"action_id": "account.action_move_out_invoice_type"}` — also require action in URL (AND)
- `{"method": "GET"}` — restrict HTTP method (AND, already existed)

**4. `display.html` — green bar now live**
- Shows current Odoo path + menu_id + action dynamically as user navigates the SPA
- Patches `history.pushState/replaceState` + `popstate` listener + 2s poll fallback
- `⚡` event badge appears in bar for 12s when a DoseMessage with "orchestration" fires

**5. `DoseRequestController` — uses shared `_instruction_matches`**
- Replaced old substring-only match with the full `match_type`-aware logic

**6. `InstructionAdmin` — updated help text**
- Documents `match_extra` AND conditions with examples

### Next Step — Create the Instruction Record
Go to **Admin → Dose → Instructions → Add**:

| Field | Value |
|---|---|
| `match_type` | `path` |
| `requestpath` | `/odoo/accounting` |
| `match_extra` | `{"menu_id": "116"}` |
| `requestmethod` | `GET` |
| `direction` | `REQ` |
| `executescript` | `OdooInvoiceNotifierService` |
| `eventKey` | `odoo_invoicing_viewed` |
| `description` | `Odoo Invoicing page detected — trigger Mattermost notification` |

### Then Test
1. Navigate to Odoo passthrough → click Invoicing in the sidebar
2. Green bar should show: `path: /odoo/accounting | menu_id: 116`
3. Server logs should show: `[ORCHESTRATION HOOK] Matched 1 instruction(s) for GET /odoo/accounting?menu_id=116...`
4. Toast should appear: `⚡ Invoice ... detected — orchestration triggered`
5. Green bar badge should flash

### If menu_id Not in URL
Odoo may put `menu_id` in the hash fragment (`#menu_id=116`) or query string depending on version.
The `_extract_odoo_ids` function searches the full `upstream_path` string including `?` and `#` — should catch both.
If it's missing, remove `match_extra` entirely and match on path only as a first test.

---

## 2026-05-09 Evening — Odoo SSO BINGO ✅

**Status**: COMPLETE  
**Branch**: main  

### Summary
Odoo SSO is fully working. Auto-login fires, session cookie is set, browser navigates to
`/pt/admin/<hostname>/web` and Odoo Invoicing loads without blank page.

### Root Causes Fixed
1. `display_credentials` not passed to display shell template → `CRED_LOGIN` undefined → SSO guard returned immediately
2. `get_request_body` replaced browser csrf_token with wrong-session token → 400 on form submit
3. `odoo_db` in `extra_config` = `tenant.schema_name` (not `odoodb`) → Odoo auth 401
4. `window.location.reload()` re-embedded SPA in Jazzmin shell → blank page; fixed to `window.location.href = data.redirect_url`
5. All `alert()` debug popups removed

### Files Changed
- `dose/odoo_sso_api.py`
- `dose/passthrough/handlers/odoo_handler.py`
- `dose/templates/admin/display.html`

### Next Session First Task
- **Mattermost SSO** (then Nextcloud SSO)
- Note: `odoo_db` stored during subscribe is wrong (stores schema name); fix subscribe_view to store `"odoodb"`

---

## BINGO — Dynamic Orchestration Pipeline (2026-05-10)

**What works end-to-end:**
1. User navigates to Odoo Customer Invoices via PT display shell
2. Odoo SPA fires `POST /web/dataset/call_kw/account.move/web_search_read` through the proxy
3. `forwarding.py` calls `check_orchestration_trigger` — Instruction id=1 matches (`contains: account.move/web_search_read`, direction=REQ)
4. `OdooInvoiceNotifierService.execute_and_save` fires (detects JSON-RPC body → navigation event)
5. `CallBackData` saved with `eventKey=odoo_invoicing_viewed` ✓
6. `DoseMessage` created → polled by display shell every 4s → toast notification appears in banner ✓
7. Mattermost post attempted (failing on `missing_config` — token not yet in polysaasts TenantApp)

**Key fixes applied this session:**
- `forwarding.py`: `get_current_tenant(request)` fallback when `request.tenant is None` (root cause of silent orchestration skip)
- `middleware.py`: `MessageMiddleware` moved before `DoseRequestController`
- `orchestration_hook.py`: debug prints + `_save_callback_data` wired correctly
- `odoo_invoice_notifier_service.py`: handles JSON-RPC body (navigation event), checks `mmauthtoken` key, resolves channel name → internal Mattermost channel_id via API
- `mysite/settings.py`: `MessageMiddleware` repositioned before `DoseRequestController`
- Instruction id=1 (polysaasts schema): `requestpath=account.move/web_search_read`, `match_type=contains`, `urllist=''` (cleared stale value)

**Remaining — Mattermost token:**
- `TenantApp` for polysaasts (PolySaaS Test Sun) Mattermost app has `status=provisioning`, `extra_config={}`
- Need to add `mmauthtoken` (or `mm_token`) + `mm_channel` to the Odoo or Mattermost TenantApp for this tenant
- Once token is configured, banner will show `Invoices page viewed — Mattermost notified ✓`

### Next Session First Task
- Configure Mattermost token in polysaasts TenantApp (Odoo or Mattermost app extra_config)
- Then: Mattermost SSO, Nextcloud SSO

---

## BINGO — Mattermost SSO ✅ (2026-05-11)

**Status**: COMPLETE
**Branch**: main
**Commits**: `b1b99f2`, `e22766c`

### What works
- `/pt/admin/mattermost/` → server-side SSO via `odooAdmin`/`PolySaaS2026!` → MMAUTHTOKEN set → redirect to `/channels/town-square` → Mattermost loads inside display shell
- Orchestration banner active on Mattermost pages
- Sidebar shows both Mattermost and Odoo passthrough icons

### Root Cause of Previous Loop (Fixed)
- Old flow: root (no token) → redirect to `/pt/admin/mattermost/login` → bridge success → navigate to root → SSO fails again → redirect to `/login` → loop
- **Fix 1**: Serve login bridge INLINE at root — no redirect to `/login` path
- **Fix 2**: After bridge login success, navigate to `/channels/town-square` (not root) — skips root intercept entirely
- **Fix 3**: `augment_outbound_headers` now injects Bearer token for ALL upstream paths (was only `/api/v4/`)
- **Fix 4**: Named trigger `mattermost` now looks up real `endpoint_url` from DB (same fix as Odoo — was constructing `https://mattermost` → Docker container)

### Credentials Stored
- `polysaast4` TenantApp (mattermost): `mattermost_login_id=odooAdmin`, `mattermost_password=PolySaaS2026!`

### Next Session First Task
- Nextcloud SSO

---

## 2026-05-15 (Early Morning — Condo) — Tenant Provisioning + Schema Migration BINGO ✅

**Status**: ✅ COMPLETE — tenant schema migrations synchronous, passthrough sidebar immediate, Secret Manager fail-fast
**Branch**: `main`

### What Was Fixed
1. **Tenant schema empty at provision time** → `_register_provisioning_synchronous` now runs Django's original `MigrateCommand` on the tenant schema after DB commit and before any provisioner
2. **Secret Manager startup hang** → added `timeout=3.0` + `retry=None` + marks client unavailable on auth failure; falls back to `.env` immediately
3. **`trigger_path` → `slug` field removal incomplete** → created migration `0048_remove_passthroughendpoint_trigger_path.py`; updated Odoo/Nextcloud provisioners and passthrough registry/path-rewrite to use `slug`
4. **Mattermost provisioning sidebar gap** → moved `_ensure_passthrough_endpoint` before early-exit on team failure so sidebar entry always created
5. **Custom migrate command recursion** → invoke Django's original `MigrateCommand` class directly instead of `call_command('migrate')`

### Verified Working
- `polysaast14` tenant created with subscription → Odoo and NextCloud passthrough icons appear immediately in sidebar
- Server starts within seconds (no Secret Manager hang)

### Pending / Follow-ups
| Priority | Task |
|----------|------|
| 1 | **Fix Mattermost provisioner silent failure** — endpoint not created at all; provisioner appears to hang/crash before `_ensure_passthrough_endpoint` runs |
| 2 | Fix Odoo passthrough client asset loading error (`owl lifecycle`) |
| 3 | Fix Nextcloud provisioner 404 — verify instance URL |
| 4 | Update `MATTERMOST_ADMIN_TOKEN` in `.env` (expired, causes 401) |

### Files Changed
- `dose/subscription_views.py`
- `dose/utils/secret_manager.py`
- `dose/services/odoo_tenant_provisioner.py`
- `dose/services/nextcloud_tenant_provisioner.py`
- `dose/services/mattermost_tenant_provisioner.py`
- `dose/passthrough/handlers/registry.py`
- `dose/passthrough/incoming_path_rewrite.py`
- `mysite/settings.py`
- `dose/migrations/0048_remove_passthroughendpoint_trigger_path.py`
- `documentation/BINGO_Tenant_Provisioning_Schema_Fixes.md`

---

## 2026-05-15 (Morning — Condo) — Mattermost Provisioning + Login Bridge BINGO ✅

**Status**: ✅ COMPLETE — Mattermost tenant provisioning works end-to-end; login bridge pre-fills both fields; redirect loop fixed
**Branch**: `main`

### What Was Fixed
1. **Mattermost admin token bypassing `sm()`** → `_get_admin_token()` now reads from `settings.MATTERMOST_ADMIN_TOKEN` (uses `sm()` → Secret Manager or `.env`) instead of direct `os.environ.get()`
2. **`trigger_path` references in `signals.py`** → replaced all remaining `trigger_path` with `slug` for `PassThroughEndpoint` lookups
3. **Expired PAT on Mattermost server** → regenerated fresh Personal Access Token as System Admin (Ollie account); updated `.env` and Secret Manager; set `$env:MATTERMOST_ADMIN_TOKEN` in PowerShell session
4. **Login bridge redirect loop** → after bridge XHR login success, redirect to `base()` (root path) instead of `/channels/town-square` directly. Root handler validates token via `augment_outbound_headers` + server-side check, then redirects to `/channels/town-square` properly.

### Verified Working
- `polysaast21` tenant subscribed → Mattermost team `polysaast21-team` created on Mattermost server
- Mattermost user `pst21` created with password pre-filled in login bridge
- Login bridge shows both email (`pst21@you.com`) and password pre-filled
- "Success! Loading..." displayed after auto-login

### Pending / Follow-ups
| Priority | Task |
|----------|------|
| 1 | **Test redirect fix on office machine** — pull latest `main`, activate venv, run server, switch to t21, click Mattermost. Should auto-login and land on Town Square without looping. |
| 2 | **Verify font controls + bell icons** remain visible after passthrough display (sidebar CSS fix from previous session) |
| 3 | **Re-authenticate gcloud** on condo machine when back — `gcloud auth application-default login` (ADC expired, causing Secret Manager retries) |
| 4 | **Fix Nextcloud provisioner 404** — verify instance URL |
| 5 | **Fix Odoo passthrough client asset loading error** (`owl lifecycle`) |

### Files Changed
- `dose/services/mattermost_tenant_provisioner.py` (token via settings, debug logging, search_path fix)
- `dose/signals.py` (trigger_path → slug)
- `dose/passthrough/handlers/mattermost_handler.py` (redirect loop fix: root path instead of /channels/town-square)
- `dose/templates/admin/includes/custom_sidebar.html` (Font Awesome icon CSS override)

### Office Machine Setup
```powershell
cd F:\PolySaaS
git pull origin main
.\venv\scripts\activate
$env:MATTERMOST_ADMIN_TOKEN = "<paste_new_token_here>"
python manage.py runserver
```
Then: switch to **POLYSAAS TEST 21** → click **Mattermost** → verify auto-login → Town Square.
