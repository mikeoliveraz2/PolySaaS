# Mattermost v6 Integration - Work Coordination

**Last Updated**: 2026-05-17 (session end before office work)  
**Branch**: main  
**Status**: WIP - Token flow working, API failure blocking completion

---

## Current Session Summary

### Completed ✅
1. **Empty token issue - FIXED**
   - Root cause: JSON-encoded empty string `""` treated as valid token
   - Solution: Token validation with JSON quote stripping in `try_root_display_shell_response()`
   - Result: Valid token `bgztkzwxsfnozqswn9uq36ezey` now obtained from login bridge

2. **Token lifecycle - FIXED**
   - Token injection: localStorage.setItem() logs show successful injection (40+ times)
   - SPA initialization: Mattermost loads with token present
   - All initial config/license APIs respond correctly with auth headers

3. **Login bridge - WORKING**
   - Auto-submit credentials from environment variables
   - XHR to Mattermost `/api/v4/users/login` succeeds
   - Token extraction from response header working
   - Token persistence through page reload implemented

### Blocked ❌
**Critical Issue**: `/api/v4/users/me/patch` returns HTTP 503 Service Unavailable
- This PATCH request is triggered by Mattermost's `updateTimeZone()` during `componentDidMount`
- When 503 occurs, client-side error handler detects server error and clears token
- Clearing token triggers redirect to login page and session loss
- Auth header logs show injection attempted, but request fails anyway

**Secondary Issues** (consequence of token clearance):
- GitHub plugin: 501 Not Implemented
- Playbooks plugin: 401 Unauthorized (likely due to cleared token)

---

## Technical Details

### Key Files Modified
- `dose/passthrough/handlers/mattermost_handler.py` - Main Mattermost handler
  - Token validation logic (JSON quote stripping)
  - Login bridge HTML/JS (auto-submit implementation)
  - Shim for token injection and request interception
  - Auth header augmentation (PATCH issue location)

### Recent Code Changes
**In `try_root_display_shell_response()`:**
```python
if token and token.strip() == '""':
    token = ''
```
This detects JSON-encoded empty string and treats as missing token.

**In `_mattermost_display_shim_html()`:**
- Added: `window.location.reload()` after token injection
- Effect: Ensures SPA initializes with token present in localStorage

**In `_serve_login_bridge()`:**
- Auto-submit enabled when credentials available from environment
- Removed debug 60-second pause
- Token extraction from response header working

### Architecture
- **Auth Flow**: Login bridge (HTML form) → XHR to `/api/v4/users/login` → Token in response header → Browser injects to localStorage → SPA reloads with token → API calls use Bearer token
- **Target**: Mattermost v6 at `https://polysaas-mattermost.onrender.com`
- **Proxy**: Passthrough at `http://localhost:8000/pt/admin/polysaas-mattermost.onrender.com/{endpoint}`
- **WebSocket**: Connects directly to Mattermost server

---

## Next Steps (Office Session)

### Priority 1: Fix /users/me/patch 503 Error
**Investigation Required:**
1. Add detailed logging to `augment_outbound_headers()` for PATCH requests
   - Log: request method, Authorization header value before/after injection, response status
   - Determine if header actually being sent or just logged

2. Verify request forwarding
   - Check if request body preserved for PATCH
   - Verify complete request reaches Mattermost backend
   - Check if Mattermost endpoint actually exists/available

3. Root cause determination
   - If auth header confirmed: Server-side issue, may need Mattermost configuration
   - If auth header missing: Fix header injection logic for PATCH
   - If request malformed: Fix PATCH request body preservation

### Priority 2: Graceful Error Handling
- Once 503 root cause understood, implement recovery:
  - Option A: Fix the underlying issue causing 503
  - Option B: Make 503 non-fatal (don't clear token on server errors)
  - Option C: Skip timezone update if it's optional feature

### Priority 3: Full Integration Testing
- Verify token persists through complete session
- Test plugin API endpoints once token issue resolved
- Validate WebSocket connectivity
- Full end-to-end Mattermost usage flow

---

## Files for Investigation
**Primary**: `dose/passthrough/handlers/mattermost_handler.py`
- `augment_outbound_headers()` function (PATCH handling)
- Request header injection logic

**Secondary**: Browser console logs showing 503 error point

---

## Git Status (Session End)
**Staged for commit:**
- `dose/passthrough/forwarding.py` (modified)
- `go-work.ps1` (new)
- `dose/passthrough/handlers/mattermost_handler.py` (merge resolved)

**Not staged:**
- `dose/subscription_views.py` (modified)
- `test_output.txt` (modified)

**Untracked** (design docs & test files):
- `PASSTHROUGH_PERSISTENT_AUTH_DESIGN.md`
- `PHASE3_COMPLETE.md`
- `PHASE3_DESIGN.md`
- `PHASE_1_IMPLEMENTATION_COMPLETE.md`
- `dose/passthrough/credential_container.py`
- `dose/passthrough/strategies/`
- Various test files

---

## Commands to Execute on Return
```powershell
cd f:\PolySaaS
git add .
git commit -m "WIP: Mattermost token flow working, PATCH endpoint 503 blocking"
git push
```
