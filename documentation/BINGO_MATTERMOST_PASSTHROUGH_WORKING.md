# BINGO: Mattermost Passthrough — End-to-End Working

**Date**: 2026-05-29  
**Status**: ✅ COMPLETE  
**Branch**: main

---

## Summary

Mattermost passthrough now works end-to-end: click sidebar → Mattermost loads in admin template div → Town Square displays with full functionality.

**Key insight**: Let Mattermost handle its own redirects. Our interference with forced `/channels/town-square` redirects was breaking Mattermost's internal team routing logic.

---

## What Was Fixed

### 1. Removed Forced Redirects
- **Before**: Root handler and plugin auth were forcing redirects to `/channels/town-square`
- **After**: Let Mattermost serve `/` and handle its own redirect based on user's team membership
- **Result**: Mattermost correctly routes to `/<team>/channels/town-square`

### 2. Credential Pre-fill on Native Login Form
- Instead of replacing Mattermost's login form with a custom bridge, we now:
  1. Let Mattermost serve its native login HTML
  2. Inject a small script that pre-populates the `loginId` and `password` fields
  3. User clicks "Sign In" manually (or we can add auto-submit later)
  4. Mattermost handles the POST and redirect naturally

### 3. IndexedDB Token Write
- After successful login via the bridge (fallback), write token to `localforage` IDB so Mattermost's Redux store hydrates correctly
- This prevents the "logout loop" where Mattermost couldn't find the token

---

## Current Flow

1. **Click Mattermost in sidebar** → `/pt/admin/polysaas-mattermost.onrender.com/`
2. **Root handler** detects no token → tries plugin auth
3. **Plugin auth succeeds** → sets MMAUTHTOKEN cookie → redirects to `/`
4. **Mattermost receives `/` with valid token** → internally redirects to user's default team
5. **Town Square loads** with full functionality

If token is invalid/expired:
1. **Mattermost serves its native `/login` page**
2. **Our pre-fill script** populates username/password fields
3. **User clicks Sign In** (or auto-submit can be added)
4. **Mattermost handles the login** and redirects appropriately

---

## Files Changed

- `dose/passthrough/handlers/mattermost_handler.py`
  - `_get_login_credentials()` — returns `(login_id, password, team_name)`
  - `process_html_response()` — injects pre-fill script instead of replacing form
  - Root handler lets Mattermost handle redirects
  - Plugin auth redirect goes to `/` not `/channels/town-square`

---

## Verification

Console output confirmed:
```
[MM ROOT] ====== PLUGIN AUTH SUCCESS ======
[MM ROOT] Existing token cookie present — letting Mattermost handle redirect
```

Browser shows:
- Town Square loaded correctly
- Team name "PolySaaS-Dev-Team" in sidebar
- All channels visible
- Welcome dialog (normal first-time UX)

---

## Remaining Improvements (Optional)

1. **Auto-submit on pre-filled form** — can add if desired
2. **Remove team name from `_get_login_credentials`** — no longer needed
3. **Clean up unused login bridge code** — `_serve_login_bridge` may be removable

---

## Architecture Lesson

**Don't fight Mattermost's internal routing.**

Mattermost's SPA has complex team/channel routing logic. Forcing specific URLs:
- `/channels/town-square` — missing team, causes "Team Not Found"
- `/<wrong-team>/channels/town-square` — causes "Team Not Found"

Letting Mattermost handle its own routing:
- User logs in → Mattermost knows their teams → redirects appropriately
- Works correctly for all user states
