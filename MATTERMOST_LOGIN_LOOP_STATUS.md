# Mattermost Login Loop Fix - Current Status

## Summary
Fixing the Mattermost auto-login loop for tenant t28. The root cause was server-side session creation invalidating browser tokens.

## Fixes Applied (Committed)

### 1. Login Bridge Auto-Submit Guard (`dose/passthrough/handlers/mattermost_handler.py`)
**Commit:** 363e50b
- Modified `DOMContentLoaded` listener to check for existing token before auto-submitting
- If token exists in localStorage or cookie, redirect directly to channels instead of creating new session
- Prevents unnecessary login attempts that revoke existing tokens

### 2. WebSocket Hardening & Auto-CORS (`dose/passthrough/handlers/mattermost_handler.py`)
**Commit:** 4b87a1f
- Added WebSocket loop breaker: after 5 rapid failures, return silent stub for 30s
- Added `_ensure_cors_allowed()` method to auto-patch Mattermost's AllowCorsFrom via API
- Calls CORS patch on first authenticated API call in `augment_outbound_headers()`

### 3. Response Headers Forwarding (`dose/passthrough/forwarding.py`)
**Commit:** 4b87a1f
- Added `X-Version-Id` and `X-Request-Id` to forwarded response headers
- Improves Mattermost SPA compatibility

## Root Cause Identified (via Shela)

**File:** `dose/services/mattermost_tenant_provisioner.py`
**Line 69:** `result['team_error'] = "Admin token verification failed — check MATTERMOST_ADMIN_TOKEN"`

This is the **tenant provisioning/bootstrap code**, not the proxy/passthrough code. The error occurs when:
1. `_get_admin_token()` retrieves `MATTERMOST_ADMIN_TOKEN` from Django settings (lines 44-48)
2. `_verify_token()` calls `GET /api/v4/users/me` to validate the token (lines 51-63)
3. If the call fails, "Admin token verification failed" is returned

**Next Step:** Investigate why the admin token verification is failing. This is likely a GCP Secret Manager access issue or an expired/invalid token.

## Testing Instructions
1. Restart Django server from worktree: `C:\Users\PC\.windsurf\worktrees\PolySaaS\PolySaaS-a136a386`
2. Click Mattermost sidebar link for tenant t28
3. Filter logs: `Select-String "MM (ROOT|AUTH|RESP)|FORWARDER|channels/town-square|LoginBridge|LOOP BREAKER"`

## Previous Fixes (Already Applied)
- `get_upstream_cookies()`: Browser cookie only, no server-side login
- `try_root_display_shell_response()`: Trust browser cookie without validation
- Shim loop breaker: Track redirects in sessionStorage
- `postprocess_upstream_response()`: Clear browser cookie on 401 via Set-Cookie header
