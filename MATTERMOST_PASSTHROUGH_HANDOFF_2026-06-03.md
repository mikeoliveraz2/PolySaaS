# Mattermost Passthrough Login Loop Handoff (2026-06-03)

## Problem Summary

PolySaaS admin-embedded Mattermost passthrough was repeatedly failing authentication UX expectations:

1. Native Mattermost login UI flashed even when passthrough/plugin auth had succeeded.
2. Users were redirected in loops between root and login bridge routes.
3. After loop reduction, users could still land on a Mattermost loading shell and not progress.
4. Runtime logs showed conflicting cookie values for `mmauthtoken` and `MMAUTHTOKEN`, and intermittent plugin endpoint 401s.

## Root Cause Pattern Observed

The key issue was inconsistent token/cookie state across paths:

1. Token validity checks could pass (`/api/v4/users/me` 200), but upstream HTML still looked like login shell content.
2. Mixed-case auth cookies (`mmauthtoken` vs `MMAUTHTOKEN`) could hold different values.
3. Forwarding merge behavior preserved stale browser cookies unless explicitly overridden.
4. Handler-side recovery logic improvements were partially undermined until cookie normalization/override was enforced.

## What Was Implemented

### 1) Login detection and loop control hardening

In `dose/passthrough/handlers/mattermost_handler.py`:

1. Tightened native login HTML detection markers to reduce false positives.
2. Added normalized token selection helper usage so lowercase token preference is consistent.
3. Removed valid-token self-redirect loop behavior in final response handling.
4. Added recovery-first behavior for stale token at root (direct session or plugin token retrieval before bridge fallback).

### 2) Login-marker response recovery behavior

In `dose/passthrough/handlers/mattermost_handler.py`:

1. When login markers appear but token validates, handler now attempts token reseed flow.
2. Added `_build_token_reseed_html(...)` to clear stale state and rewrite both auth cookie casings before bouncing to root.

### 3) Upstream cookie normalization fix (latest)

In `dose/passthrough/handlers/mattermost_handler.py`:

1. Updated `filter_cookies_for_upstream(...)`:
   - Login/logout requests strip Mattermost token cookie as before.
   - Non-login requests now normalize both `mmauthtoken` and `MMAUTHTOKEN` to the selected token.
2. Added `override_upstream_cookies(...)`:
   - Runs after merge path in forwarder.
   - Forces both cookie keys to identical selected token for non-login URLs.

### 4) Runtime blocker fix

In `dose/passthrough/handlers/mattermost_handler.py`:

1. Fixed indentation in plugin-auth-success branch causing `IndentationError`.

## Verification Performed

1. Syntax/diagnostic checks passed for changed passthrough files after edits.
2. Local Django shell test with intentionally conflicting cookie values showed normalization working:
   - `filtered {'mmauthtoken': 'lowerOK', 'MMAUTHTOKEN': 'lowerOK'}`
   - `override {'mmauthtoken': 'lowerOK', 'MMAUTHTOKEN': 'lowerOK'}`
3. Previous stale-token recovery simulation had already shown recovery branch execution and 200 outcome after plugin fallback.

## Current State

1. Redirect-loop behavior has been significantly reduced/hardened.
2. Cookie mismatch propagation to upstream is now explicitly normalized/overridden in handler paths.
3. Remaining risk is mainly runtime behavior variance in live tenant/browser context (cached cookies/session artifacts and real upstream HTML behavior).

## Recommended Next Steps (When You Resume)

1. Live-verify tenant flow for `POLYSAAST122` at:
   - `/pt/admin/polysaas-mattermost.onrender.com/`
2. Capture fresh logs for one clean attempt (new browser profile/incognito preferred):
   - Confirm no repeated mismatch warnings after normalization.
   - Confirm root HTML no longer resolves to login/loading shell loop state.
3. If loading shell still appears:
   - Add temporary debug around native-login HTML classifier result and root-shell response body markers.
   - Verify which exact upstream path/body is being served at the stuck point.
4. Optional hardening:
   - Mirror override behavior in any non-standard fetch path if discovered outside standard forwarder flow.
   - Add focused tests for mixed-case cookie conflict and login-marker-with-valid-token path.

## Files Touched During This Cycle

1. `dose/passthrough/handlers/mattermost_handler.py`
2. `mysite/urls.py` (already modified in working tree and included in commit per user request)

## Handoff Note

Work has been committed and pushed so pickup can continue from another location/device without loss of context.
