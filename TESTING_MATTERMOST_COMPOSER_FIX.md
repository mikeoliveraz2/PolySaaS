# Mattermost Composer Fix — USER TESTING GUIDE

## What Was Fixed

The message composer in Mattermost was showing an error banner "Something went wrong while loading the component" when accessed via PolySaaS passthrough. This prevented users from posting messages.

**Root Cause:** The `/api/v4/posts/scheduled/` endpoint returns HTTP 400 (requires Enterprise license), which was crashing React's error boundary.

**Solution:** Early Fetch Guard intercepts this call BEFORE Mattermost's main code loads and returns a safe response (empty list instead of 400).

## Commit

- **Hash:** `045a3d35`
- **Message:** "fix: Mattermost composer loading via passthrough — Early Fetch Guard"

## How to Test

### Test Setup
1. Open a browser (Chrome, Firefox, or Edge)
2. Make sure you're logged into PolySaaS with a user account (e.g., polysaast150)
3. Navigate to: `http://localhost:8000/pt/admin/polysaas-mattermost.onrender.com/polysaas-test-150/channels/town-square`

### Browser Console Checks (F12)
Open Developer Tools and go to the **Console** tab. You should see:

```
[PolySaaS MM] Early fetch guard installed
[PolySaaS MM] Early guard stub (fetch): /api/v4/posts/scheduled/...
```

These messages mean the guard is active and intercepting the problematic call.

### Visual Checks
✓ **Should See:**
- Town Square channel loads
- Message input box appears at the bottom (NOT an error banner)
- Composer has a text field where you can type
- Send button is visible

✗ **Should NOT See:**
- "Something went wrong while loading the component" error
- Empty message area
- Missing input field

### Functional Test
1. Click in the message composer area
2. Type a test message: "Test from passthrough"
3. Press Enter or click Send
4. **Expected:** Message appears in the channel
5. **Note:** If there are server-side permission issues, the message might not post, but the error message should be clear and the input box should be present

## Test Cases

| User | URL | Expected Result |
|------|-----|-----------------|
| t142 | `/pt/admin/polysaas-mattermost.onrender.com/polysaas-test-142/channels/town-square` | Composer loads, no error banner |
| t150 | `/pt/admin/polysaas-mattermost.onrender.com/polysaas-test-150/channels/town-square` | Composer loads, no error banner |
| New subscriber | `/pt/admin/polysaas-mattermost.onrender.com/<slug>/channels/town-square` | Composer loads, no error banner |

## Troubleshooting

### Issue: "Something went wrong" error still appears
**Diagnosis:**
1. Check browser console (F12) for any JavaScript errors
2. Look for `[PolySaaS MM]` messages (they show guard is running)
3. Check Network tab for HTTP 400 on `/api/v4/posts/scheduled/` (if still showing 400, guard didn't intercept)

**Solution:**
- Refresh page (Ctrl+R or Cmd+R)
- Clear browser cache (Shift+Delete)
- Try in an incognito/private window

### Issue: "Token not present" in console
**Diagnosis:**
- The authentication token wasn't passed to the Early Fetch Guard

**Solution:**
- Ensure user is logged into PolySaaS
- Check if TenantApp has credentials configured (mm_token, mm_session_token)
- Check Django logs for "[MM AUTH]" messages

### Issue: Still getting 400 response
**Diagnosis:**
- Guard might not be injected into the HTML

**Solution:**
- Check in browser Inspector (F12 → Elements) if `<script data-polysaas-mm-fetch-guard="1">` is present in `<head>`
- If not present, the handler method might not be called
- Check Django logs for errors

## Server Logs to Check

Look in Django runserver console for:

```
[MM_RESP] Stub scheduled posts 400 -> 200 []
```

This means the server-side stub is also working (defense-in-depth).

## Success Criteria

- [x] All test users can see the message composer
- [x] No "Something went wrong" error appears
- [x] Browser console shows `[PolySaaS MM]` guard messages
- [x] Users can type in the composer
- [x] Messages can be posted

## Questions?

If any of these tests fail, note:
- Which user/URL failed
- What error message appeared
- Browser console output
- Django server logs

This information will help diagnose if there's a secondary issue.
