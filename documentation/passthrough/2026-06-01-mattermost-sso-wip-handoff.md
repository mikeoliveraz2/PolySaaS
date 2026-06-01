# Mattermost SSO WIP Handoff - 2026-06-01

## Why this handoff exists

Mattermost passthrough SSO was working from the 2026-05-31 BINGO baseline, except repeat access could fall through to the native Mattermost login. We believed stale browser cookies/session state were causing Mattermost's React SPA to redirect to `/login`.

On 2026-06-01 we tried several fixes, but the flow is not back to a stable BINGO state. Current WIP should be treated as a checkpoint for later analysis, not a verified fix.

## Known good baseline

- Commit `d191f2a3` - `BINGO: Mattermost login bridge auto-SSO + Town Square`
- Follow-up doc hash commit `d4aa8bc6`
- In that state:
  - `/pt/admin/<mattermost-host>/login` served the PolySaaS login bridge.
  - Plugin auth could issue a Mattermost token.
  - The user reached Town Square.
  - Remaining issue: repeat access sometimes fell into native Mattermost login.

## Current observed behavior

Latest test behavior before this handoff:

- Green orchestration bar renders.
- Action path remains `/`.
- Mattermost starts to load Town Square, then hangs.
- Server logs show token validation succeeds:
  - `[MM AUTH] Token validation users/me -> HTTP 200`
  - `[MM ROOT] IDB cleared - forwarding to Mattermost /`
  - `MMAUTHTOKEN` and `mmauthtoken` cookies are present.
- Mattermost API calls can succeed, e.g.:
  - `POST /api/v4/channels/members/me/view -> HTTP 200`
- Despite valid auth, the SPA does not complete the Town Square render.

## What was changed today

File touched:

- `dose/passthrough/handlers/mattermost_handler.py`

Important WIP changes:

- Restored the handler near the `d191f2a3` BINGO baseline during debugging.
- Added plugin-first root entry logic:
  - fresh root entry calls `_get_plugin_auth_token()` before trusting an existing browser cookie.
  - plugin success sets `MMAUTHTOKEN` / `mmauthtoken`.
  - plugin success redirects to `/?plugin_booted=1` to avoid looping.
- Added IndexedDB cleanup before Mattermost SPA hydration:
  - deletes `localforage` / `keyvaluepairs` / `persist:storage`.
  - avoids merging old Redux state back into `persist:storage`.
- Removed hardcoded Town Square redirects in the login bridge:
  - redirects now go to Mattermost root `/`.
- Removed use of `mm_team_name` / `team_name` from login prefill debug flow.
- Added `team_not_found` recovery handling:
  - server side: `?type=team_not_found` forces plugin auth + IDB wipe.
  - client side: React-router navigation to `type=team_not_found` forces clean re-entry.
- Added `_mmOrigReplace` to avoid self-intercept loops when redirecting away from Mattermost's native `/login` route.

Temporary/debug files created:

- `check_mm_config.py`
- `fix_mm_oidc_flag.py`
- `dose/passthrough/handlers/mattermost_handler.py.bak3`
- `dose/passthrough/handlers/mattermost_handler.py.bak4`

Existing `.bak` files were also changed during the debugging session.

## Database/config action taken

`fix_mm_oidc_flag.py` was used to remove `mattermost_oidc_enabled` from active Mattermost `TenantApp.extra_config` records because that flag appeared to disable login bridge auto-submit behavior.

## Current hypothesis

Authentication itself is probably not the blocker now. The plugin/cookie token validates against `/api/v4/users/me`, and Mattermost API requests are being accepted.

The remaining hang is likely one of:

- Mattermost SPA still rehydrates incomplete or malformed Redux/localforage auth state.
- The injected shim's minimal `persist:storage` shape is not the shape Mattermost expects after a clean IDB wipe.
- The admin-template wrapped environment is interfering with SPA boot completion after auth succeeds.
- A JavaScript console error is occurring after the token is accepted; browser console evidence is needed next.

## Recommended next restart point

Do not keep layering fixes. Start from one of these two clean approaches:

1. Reset `dose/passthrough/handlers/mattermost_handler.py` to `d191f2a3`, then reapply only the smallest repeat-access fix.
2. Keep the current WIP but debug in the browser console, focusing on the first JavaScript exception after:
   - plugin auth success
   - IDB delete
   - `/?plugin_booted=1`
   - injected shim load

The fastest path is likely option 1.

## Session 2 changes (2026-06-02, pre-office)

### Root cause identified: logout response triggering Redux LOGOUT_SUCCESS

Browser console + HAR analysis revealed the `ERR_ABORTED` reload loop:

1. Mattermost SPA calls `/api/v4/users/logout` via fetch and XHR.
2. Shim blocked the request but returned `Response(null, {status: 200})` -- a **success**.
3. Mattermost Redux middleware dispatched `LOGOUT_SUCCESS`, clearing session from Redux store.
4. With no session, SPA entered tight `window.location.href` reload loop (~1/sec).

### Fixes applied

File: `dose/passthrough/handlers/mattermost_handler.py`

1. **Fetch logout block**: Changed from `200 OK` to `403 Forbidden` with JSON error body `{id: "api.user.logout.disabled", message: "Logout disabled by SSO policy"}`. Redux sees logout *failed* and keeps the session.

2. **XHR logout block**: Changed from silently setting `_blocked = true` (no response) to using `_logoutBlocked` flag. The `send()` override now synthesizes a full 403 response with proper `readyState=4`, fires `onreadystatechange`/`onload`/`load`/`loadend` events.

3. **Unicode fix**: Replaced all `→` (U+2192) and `—` (U+2014) characters with ASCII equivalents (`->` and `--`) throughout the file. Windows cp1252 console encoding cannot encode these, causing `UnicodeEncodeError` crashes in `print()` statements.

### IndexedDB fix (from end of session 1)

Changed `indexedDB.open('localforage', 2)` to `indexedDB.open('localforage')` in 3 locations within the injected shim. The hardcoded version 2 caused `VersionError` when the browser already had a different version, preventing token writes to IDB entirely. After this fix, `[PolySaaS MM IDB] persist:storage merged` logs confirmed successful writes.

### Status

- Token acquisition: working (session token via `/api/v4/users/login`)
- Token storage to IDB: working
- Logout blocking: now returns 403 (untested in browser -- apply this and test at office)
- Unicode crash: fixed

### Next step at office

1. Clear browser data for localhost (or incognito)
2. Click Mattermost in sidebar
3. Check console for:
   - `[PolySaaS MM] Blocked logout (403)` messages (confirms new logic is active)
   - Absence of `ERR_ABORTED` reload loop
   - `has_session: true` in plugin diagnostics
4. If Town Square renders, this is the new baseline for BINGO

## Verification commands run

```powershell
python -m py_compile dose\passthrough\handlers\mattermost_handler.py
```

Result: compile succeeded. Existing Python `SyntaxWarning` messages about escape sequences remain, but no syntax error.

Cursor lints on `mattermost_handler.py`: no linter errors reported.
