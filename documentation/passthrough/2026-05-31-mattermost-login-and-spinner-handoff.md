# Handoff — 2026-05-31 evening: Login fix + Mattermost Town Square (spinner remaining)

**Status:** NOT a BINGO. Login is fixed and Mattermost now navigates to Town Square,
but the Mattermost SPA is **stuck on the loading spinner** at
`/pt/admin/<mm-host>/channels/town-square`. Pick up here in the morning.

## What was wrong and what got fixed today

### 1. PolySaaS login outage (FIXED)
- **Symptom:** Every login (including a freshly created superuser) failed. The login
  POST returned HTTP 200 (form re-render), `authenticate()` was never called, session
  stayed empty.
- **Root cause:** allauth was upgraded to **65.14.3** during today's Odoo/dependency
  work. In allauth 65, `LoginForm._setup_password_field()` (`allauth/account/forms.py`
  ~line 126) **deletes the password field from the LOGIN form** when
  `ACCOUNT_SIGNUP_FIELDS` has no `password1`. Our setting was `['email*']`, so the login
  form went passwordless → submitted password ignored → `{"login": ["Invalid login."]}`.
  Config hadn't changed; the allauth version had. Older allauth didn't couple these.
- **Proof:** Direct `authenticate(username='mikeoliver', password=...)` returned the user,
  but `LoginForm.fields` was `['login', 'remember']` (no `password`) and
  `is_valid()` was False. After the fix, fields became `['login', 'password', 'remember']`
  and `is_valid()` True.
- **Fix (`mysite/settings.py`):**
  ```python
  ACCOUNT_SIGNUP_FIELDS = ['username*', 'email*', 'password1*', 'password2*']
  ```
- **Side effect to review:** This also drives allauth's **signup** form. If the
  subscribe flow uses allauth's signup form, it now requires username + email +
  password + confirm. If email-only signup is desired, the minimal alternative that
  still fixes login is `['email*', 'password1*']`.

### 2. Mattermost: could not get past plugin to Town Square (FIXED)
gpt-era commits between this morning's BINGO (`5ea7d47f`) and now introduced three
regressions in `dose/passthrough/handlers/mattermost_handler.py`. Reverted:
- Redirect target was changed to `/` (root); **restored to `/channels/town-square`**
  in both the login bridge JS and the plugin-auth redirect HTML.
- **Removed** the `defer` attribute injected onto `main.*.js` / `remote_entry.js`
  bootstrap bundles (changed MM bootstrap order).
- **Removed** the blocking synchronous `/api/v4/users/me` validation on root load
  (stalled/looped on Render cold-starts). Restored BINGO behavior: token present →
  let Mattermost handle it.
- **Kept:** `format=old` on `/api/v4/config/client`, cookie isolation. `forwarding.py`
  (shared Odoo hooks) intentionally untouched.

## REMAINING ISSUE (for the morning): Mattermost stuck on loading spinner

After login + redirect to `/channels/town-square`, the Mattermost SPA shows the
loading spinner and does not finish booting.

### Where to start
1. **Browser console** on the stuck page — look for `[PolySaaS MM]` shim logs:
   - Did the shim load? (`Full shim loaded, proxy=...`)
   - Is the token present? (`Token set in localStorage + cookie + IDB, len=...`)
   - Are `fetch`/XHR being routed via `toProxy()`?
2. **Network tab / server log:**
   - Does `GET /api/v4/users/me` (through the proxy) return **200** or **401**?
   - Does `GET /api/v4/config/client?format=old` return 200 with rewritten
     `SiteURL`/`WebsocketURL`?
   - Does the **WebSocket** connect (direct to upstream `wss://<mm-host>`) or fail/loop?
   - Are the `main.*.js` bundles loading 200 from the upstream origin?
3. **Shim ordering tension (key suspect):** removing `defer` fixed the Town Square
   redirect but the spinner may be the *other* side of that trade-off — the shim must
   patch `fetch`/`XHR`/`WebSocket` and set `__webpack_public_path__` **before** the MM
   bundle executes, while `#root` must exist when React mounts. Investigate a way to
   guarantee shim-runs-first WITHOUT reintroducing the redirect break (e.g. inject shim
   as the very first element in `<head>` and keep bundles non-deferred, or verify the
   shim's history/location patches aren't fighting MM's router at `/channels/...`).
4. Confirm the upstream Mattermost on Render is awake (cold start can mimic a hang).

### Useful references
- Handler: `dose/passthrough/handlers/mattermost_handler.py`
  - `try_root_display_shell_response` (root intercept / token / plugin auth)
  - `_serve_login_bridge` (login bridge JS + redirect target)
  - `_mattermost_display_shim_html` (the client shim: fetch/XHR/WS patches,
    `_writeTokenToIDB`, `/login` interception, loop breakers)
  - `process_html_response` (URL rewriting, shim injection)
- Last working full BINGO of MM: commit `5ea7d47f`.

## Commits / git state
- **`30a3dd1c`** — "Fix login outage (allauth 65 passwordless form) and Mattermost
  Town Square regression" (login + MM handler). Pushed to `origin/main`.
- **`fdd1f1a8`** — "refactor(mattermost): improve token handling and redirect logic":
  an **unpushed local** commit that existed before tonight's fix; it rode along in the
  push (range `3b9dd9aa..30a3dd1c`). **Check with Shela** that this was expected
  (possible concurrent work from the other machine/session).
- Backups: `mysite/settings.py.bak`, `dose/passthrough/handlers/mattermost_handler.py.bak`.

## Files touched today (this session)
- `mysite/settings.py` (+ `.bak`)
- `dose/passthrough/handlers/mattermost_handler.py`
