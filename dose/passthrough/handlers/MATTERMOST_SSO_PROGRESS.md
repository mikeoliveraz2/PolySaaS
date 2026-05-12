# Mattermost SSO / Auto-Login — Progress Notes

**Last Updated**: 2026-05-11  
**Status**: ✅ WORKING — Server-side SSO active, auto-login functional

---

## Current State (What's Actually Working)

### ✅ Server-Side SSO (Primary Flow)
**Path**: User clicks Mattermost in sidebar → `/pt/admin/mattermost/` → auto-login → Town Square

1. `try_root_display_shell_response` detects no `MMAUTHTOKEN` cookie
2. Calls `get_upstream_cookies()` → POST to Mattermost `/api/v4/users/login` with credentials from `TenantApp.extra_config`
3. Receives `MMAUTHTOKEN` from upstream
4. Sets cookie on browser, redirects to `/channels/town-square`
5. Mattermost SPA loads with valid session — **no form displayed, straight to Town Square**

**Credentials stored in** `TenantApp.extra_config`:
- `mattermost_login_id` = `odooAdmin`
- `mattermost_password` = `PolySaaS2026!`

### ⚠️ Login Bridge (Fallback Only)
The bridge (`_serve_login_bridge`) is served inline at root only when server-side SSO fails. Currently:
- Auto-submit is **DISABLED** (lines 206-211 commented out)
- Manual click required if SSO fails
- This is a safety fallback, not the primary path

### ✅ Shim Injection
- `Authorization: Bearer <token>` header injected for all API calls
- WebSocket uses live token from `localStorage`
- Static assets route correctly through proxy

---

## Previous Issues (Fixed)

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Login loop | Root redirect → `/login` → bridge → navigate to root → SSO fails again → loop | Serve bridge inline at root; navigate to `/channels/town-square` after success |
| Token not injected | `augment_outbound_headers` only injected for `/api/v4/` | Now injects for ALL upstream paths |
| Bad endpoint URL | Named trigger `mattermost` constructed `https://mattermost` instead of real URL | Lookup `endpoint_url` from DB (same fix as Odoo) |

---

## Next Steps / For Other AI

1. **Nextcloud SSO** — apply same server-side SSO pattern
2. **Re-enable bridge auto-submit** (optional) — uncomment lines 206-211 if you want the bridge to auto-submit when SSO fails
3. **Remove bridge entirely** (optional) — if server-side SSO is reliable, the bridge can be deleted

---

## Files of Interest
- `dose/passthrough/handlers/mattermost_handler.py`
  - `try_root_display_shell_response` — SSO entry point
  - `get_upstream_cookies` — server-side login to Mattermost API
  - `_serve_login_bridge` — fallback form (auto-submit disabled)
  - `_mattermost_display_shim_html` — client-side token injection
  - `augment_outbound_headers` — Bearer token injection for API calls

## Diagnostic Markers
- Server logs: `[MM SSO]`, `[MM_AUTH]`, `[MM Shim]`, `[FORWARDER]`, `=== LOGIN FORWARD DEBUG ===`
- Browser console: `[LoginBridge]`, `[PolySaaS MM]`
