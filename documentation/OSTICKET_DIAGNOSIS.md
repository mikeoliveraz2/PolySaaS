# OS Ticket Login & Passthrough Diagnosis

## Current Implementation Analysis

### 1. Login Flow (`apply_latest_capture` in `dose/polysniffer/views.py`)

**Steps:**
1. ✅ GET login page → Extract CSRF token from `__CSRFToken__` input
2. ✅ AJAX POST with payload:
   - `__CSRFToken__`: CSRF token
   - `do`: "scplogin"
   - `userid`: endpoint.auth_username
   - `passwd`: endpoint.auth_password
   - `ajax`: "1"
3. ✅ Capture cookies from session (looks for `OSTSESSID` or `SSSESSID`)
4. ✅ Save cookies to `endpoint.discovered_subpaths['cookies']`
5. ✅ Also set cookie in persistent session via `get_osticket_session()`

**Potential Issues:**
- Line 865: Saves ALL cookies, but might need to filter
- Line 872-876: Sets cookie with explicit `domain` and `path` - this might be too restrictive
- Cookie might expire between login and passthrough use

### 2. Passthrough Flow (`generic_passthrough_views.py`)

**Steps:**
1. ✅ Checks `endpoint.discovered_subpaths['cookies']` for fresh cookies
2. ✅ If found, sets them in persistent session (line 849-854)
3. ✅ If NOT found, syncs from browser cookies (line 875-886)
4. ✅ Uses persistent session for all OS Ticket requests

**Potential Issues:**
- Line 853: Sets cookies without domain/path (good - matches working code)
- Line 833: Refreshes endpoint from DB (good - gets latest cookies)
- BUT: The cookie might not be sent correctly if domain/path don't match

## Key Findings

### What Should Work:
1. ✅ Login flow looks correct (matches browser behavior)
2. ✅ Cookie capture looks correct (gets OSTSESSID or SSSESSID)
3. ✅ Cookie storage looks correct (saves to discovered_subpaths)
4. ✅ Cookie retrieval looks correct (checks discovered_subpaths first)

### Potential Problems:

1. **Cookie Domain/Path Mismatch**
   - Login saves cookie with explicit domain/path (line 872-876)
   - Passthrough sets cookie without domain/path (line 853)
   - **Fix**: Make both consistent - don't set domain/path in login either

2. **Cookie Not Persisting**
   - Persistent session might not be shared correctly
   - **Check**: Verify `get_osticket_session()` returns same session instance

3. **Timing Issue**
   - Cookie might expire between login and passthrough
   - **Check**: How long between login and passthrough request?

4. **Cookie Format**
   - OS Ticket might require specific cookie attributes (HttpOnly, Secure, SameSite)
   - **Check**: What attributes does the real browser cookie have?

## Recommended Test Script Results to Look For:

When you run `run_osticket_test.py`, check:

1. **Login Success Rate**: How many of 10 logins succeed?
2. **Cookie Capture**: Does it always capture OSTSESSID/SSSESSID?
3. **Cookie Value**: Is the cookie value consistent across attempts?
4. **Dashboard Access**: After login, can it access dashboard.php?
5. **Access Denied**: Does dashboard show "access denied" even with cookie?

## Next Steps Based on Test Results:

### If Login Fails:
- Check CSRF token extraction
- Check credentials
- Check login response (what does OS Ticket return?)

### If Login Succeeds But Passthrough Fails:
- Cookie domain/path issue (most likely)
- Cookie not being sent in passthrough request
- Cookie expired between login and passthrough

### If Dashboard Test Shows "Access Denied":
- Cookie is captured but not valid
- Cookie needs additional attributes
- OS Ticket requires additional headers/cookies

## Quick Fixes to Try:

1. **Remove explicit domain/path from login cookie setting** (line 872-876):
   ```python
   # Instead of:
   persistent_session.cookies.set(session_cookie_name, session_cookie_value, domain=..., path=...)

   # Use:
   persistent_session.cookies.set(session_cookie_name, session_cookie_value)
   ```

2. **Verify cookie is being sent in passthrough**:
   - Add logging to show exact cookies sent in request
   - Compare with what browser sends

3. **Test cookie freshness**:
   - Login, immediately test passthrough
   - If it works, then wait 30 seconds and test again
   - This will show if it's a timing/expiration issue

