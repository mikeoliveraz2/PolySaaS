# Mattermost Passthrough SSO — Zero-Cache Working State
**Date:** 2026-06-04  
**Status:** WORKING (first click, fresh cache)

## Current Behavior
- **First click from PolySaaS admin → Mattermost:** ✅ Town square loads successfully
- **Repeated clicks after caching:** ❌ "Team Not Found" error
- **After browser cache clear:** ✅ Town square loads again (one time)
- **Repeated clicks after that:** ❌ "Team Not Found" error

## Root Cause Identified
The Mattermost SPA caches state in localStorage/IndexedDB (team ID, config, etc.). On subsequent clicks, the stale cached state causes the SPA to attempt team-based routing, which fails because:
1. No team was explicitly selected in PolySaaS
2. Mattermost tries to load a "LastTeamId" from cache
3. That team membership fails or doesn't exist in the correct context
4. SPA displays "Team Not Found"

## Solution Approach (WIP)
Need to implement aggressive cache-busting and localStorage clearing **on every redirect** to force the Mattermost SPA to always load fresh from the plugin auth state, not cached team state.

## Files Modified in This Session
- `dose/passthrough/handlers/mattermost_handler.py` — Added token validation, cache-bust params, localStorage clearing
- **REVERTED:** All experimental changes to keep this as the known-good baseline

## Next Steps
1. Implement client-side cache invalidation in the shim
2. Add `?t=<timestamp>` cache-bust to all Mattermost redirects
3. Force-clear localStorage on every plugin auth cycle
4. Test repeated clicks without cache clear

## Notes
- Credentials are confirmed good (`mm_login_id`, `mm_password` present in `extra_config`)
- Plugin auth returns valid 26-character token
- Direct login via POST `/users/login` should work but needs investigation
- "No team logic" directive must be preserved — team resolution is NOT part of passthrough
