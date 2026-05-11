# Mattermost SSO / Auto-Login — Progress Notes

## Status: Partial — login XHR succeeds, but post-redirect SPA bounces back to `/login`.

## What works
- **Server-side SSO** (`try_root_display_shell_response`): when no `MMAUTHTOKEN` cookie, calls `get_upstream_cookies` to log in server-side using credentials from `extra_config`, sets the cookie on the browser, and redirects to root.
- **Login bridge fallback** (`_serve_login_bridge`): clean static HTML form embedded inside the PolySaaS admin template (via `_wrap_in_admin_template`). Pre-populates `mattermost_login_id` / `mattermost_password` from `extra_config`. Auto-submit currently **disabled** for debugging — manual click only.
- **Bridge XHR** to `/api/v4/users/login` returns **200 with a `Token` header**. Token + cookie + `localStorage["MMAUTHTOKEN"]` + `localStorage["storage:MMAUTHTOKEN"]` all written.
- **Shim history hook**: intercepts client-side `pushState`/`replaceState` to `/login` and forces a real GET so the bridge serves on bounce-backs (instead of the SPA's React form).
- **Cookie hygiene on login path**:
  - `filter_cookies_for_upstream` strips `MMAUTHTOKEN` on `/api/v4/users/login` and `/logout`.
  - `get_upstream_cookies` early-returns `{}` on those paths.
  - `augment_outbound_headers` skips `Authorization` injection on those paths.
  - Result: login XHR reaches Mattermost completely clean (no stale Bearer token poisoning the request).
- **Shim token source**: prefers fresh browser-set `MMAUTHTOKEN` cookie over the cached server token, so the bridge's freshly-issued token is what ends up in localStorage.

## What's broken
After bridge XHR returns 200 + token and the page redirects to root:
1. Mattermost HTML serves with shim injecting fresh token into localStorage.
2. ~23 Mattermost JS chunks load.
3. Mattermost SPA initialises, then **bounces back to `/login`**.
4. **No 4xx responses observed** in the network tab during the bounce-back (per user report).

## Hypothesis
Mattermost's React app uses **Redux + Redux Persist**. The full user/team/preferences state lives in `localStorage["persist:root"]`. Our bridge populates only `MMAUTHTOKEN`, never `persist:root`.

When the SPA loads, it:
- Reads `persist:root` → empty / no user.
- Decides client-side "not logged in" without making an auth API call (explains absence of 401s).
- Routes to `/login`.

## Recommended next step (not yet implemented)
**Abandon the custom bridge.** Instead:
1. Let Mattermost's **native** login form render unmodified.
2. Inject a small script into the Mattermost login HTML that:
   - Fills `#input_loginId` and `#input_password-input` with values from a server-rendered `MM_LOGIN_ID` / `MM_PASSWORD`.
   - Clicks `#saveSetting` (or the native Sign-In button).
3. Mattermost's own React/Redux flow handles the submit, populates `persist:root`, and routes correctly.

This removes the need for `_serve_login_bridge`, the history-hook hard-redirect, and most of the cookie hygiene workarounds.

## Files of interest
- `dose/passthrough/handlers/mattermost_handler.py`
  - `try_root_display_shell_response` — SSO + bridge fallback
  - `_serve_login_bridge` — current debug bridge (auto-submit disabled)
  - `_mattermost_display_shim_html` — shim with history hook + token source preference
  - `augment_outbound_headers`, `get_upstream_cookies`, `filter_cookies_for_upstream` — login-path cookie hygiene
- `dose/passthrough/middleware.py` — `_wrap_in_admin_template` (used by the bridge)
- `dose/templates/admin/passthrough_embed.html` — admin template; embed_body is rendered directly (no iframe).

## Diagnostic commands
- Server log markers: `[MM SSO]`, `[MM_AUTH]`, `[MM Shim]`, `[FORWARDER]`, `=== LOGIN FORWARD DEBUG ===`
- Browser console markers: `[LoginBridge]`, `[PolySaaS MM]`
- Pending verification: confirm whether the bounce-back from Mattermost SPA produces **any** 4xx response or is purely client-side routing.
