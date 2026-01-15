# OS Ticket Passthrough - Current Status & Next Steps

## What We've Tried

1. ✅ **AJAX Login** - Captures cookie via requests library (works)
2. ✅ **Cookie Storage** - Saves to `endpoint.discovered_subpaths['cookies']` (works)
3. ✅ **Cookie in Browser** - Sets cookie via `Set-Cookie` header after login (should work)
4. ✅ **Cookie Sync** - Syncs from browser to session (like osticket_admin_view)
5. ✅ **Manual Cookie Header** - Sets Cookie header manually to ensure it's sent
6. ✅ **Referer Header** - Sets Referer to OS Ticket domain
7. ❌ **Still Getting "Access Denied"**

## Core Issue

The cookie is being captured and sent, but OS Ticket is still rejecting it. Possible reasons:

### 1. **Cookie Validation**
OS Ticket might be checking:
- **IP Address** - Cookie might be tied to the IP that logged in
- **User-Agent** - Must match exactly
- **Session State** - Cookie might need to be used immediately after login
- **CSRF Token** - Must match the session

### 2. **Cookie Attributes**
The cookie might need specific attributes:
- `HttpOnly` flag
- `Secure` flag (if HTTPS)
- `SameSite` attribute
- Exact `domain` and `path` matching

### 3. **Request Sequence**
OS Ticket might require:
- Visiting login page first (even if already logged in)
- Specific headers in exact order
- Following redirects properly

## What We Need to Check

### Diagnostic Endpoint Output
Visit: `http://localhost:8000/admin/polysniffer/test-osticket/`

Look for:
- `browser_has_session_cookie`: Should be `true`
- `has_fresh_session_cookie`: Should be `true`
- `session_cookies_before_request`: Shows what's being sent
- `has_access_denied`: Whether OS Ticket rejects it
- `response_preview`: What OS Ticket actually says

### Compare with Working Code
The `osticket_admin_view` works. Key differences:
- Uses browser cookies directly (user logs in via browser first)
- Minimal headers
- Syncs FROM browser TO session

## Potential Solutions

### Option 1: Use Browser Login Flow
Instead of server-side AJAX login, have user log in via browser:
1. User clicks "Login to OS Ticket" button
2. Opens OS Ticket login page in new window
3. User logs in manually
4. Browser gets cookie automatically
5. Passthrough uses browser cookie

### Option 2: Fix Cookie Attributes
Ensure cookie has exact same attributes as browser cookie:
- Check what browser cookie looks like (DevTools)
- Match domain, path, HttpOnly, Secure, SameSite exactly

### Option 3: Use Same Session
Instead of capturing cookie and using later, use the SAME requests.Session:
- Login and immediately use that session for passthrough
- Don't save/restore cookies, just keep session alive

### Option 4: Check OS Ticket Configuration
OS Ticket might have:
- IP whitelist/blacklist
- Session timeout settings
- CSRF protection that's too strict

## Immediate Next Steps

1. **Check Diagnostic Output** - See what's actually happening
2. **Compare Browser Cookie** - Use DevTools to see what browser cookie looks like
3. **Try Immediate Use** - Use cookie immediately after login (within 1 second)
4. **Check OS Ticket Logs** - See what OS Ticket server logs say

## Quick Test

Run this in browser console after clicking "Auto-Login":
```javascript
// Check if cookie is set
document.cookie

// Should see OSTSESSID or SSSESSID
```

Then immediately try accessing OS Ticket through passthrough.

