# Use PolySniffer to Debug OS Ticket "Access Denied"

## Quick Steps

### Step 1: Open PolySniffer Dashboard
1. Go to: `http://localhost:8000/dose/polysniffer/`
2. Should see dashboard (may be empty initially)

### Step 2: Click "Sniff" on OS Ticket Endpoint
1. Go to: `http://localhost:8000/admin/dose/passthroughendpoint/`
2. Find OS Ticket endpoint in the list
3. Click the **"🔍 Sniff"** button
4. This opens PolySniffer interface

### Step 3: Try Accessing OS Ticket
1. In another tab, go to: `http://localhost:8000/admin/osticket/`
2. Try to login or navigate
3. Watch what happens

### Step 4: Check Captured Traffic
1. Go back to: `http://localhost:8000/dose/polysniffer/`
2. You should see captured requests
3. Look for:
   - **Status codes** (422? 403? 401?)
   - **Response body** - does it say "access denied"?
   - **Headers** - what headers are being sent?
   - **Cookies** - are session cookies present?

## What to Look For

### If you see 422 status:
- Check POST data - is `ajax=1` present?
- Check headers - are all required headers there?
- Compare with the fix we applied

### If you see 403/401 status:
- Authentication issue
- Check if cookies are being forwarded
- Check if OAuth2 is still being required

### If response body says "access denied":
- This is from OS Ticket server
- Check what the actual error message is
- Look at the full response in PolySniffer

## Alternative: Use PolySniffer "Sniff" Button

The "Sniff" button should:
1. Open PolySniffer interface
2. Pre-fill the OS Ticket URL
3. Allow you to navigate and capture traffic

**Try clicking the Sniff button and see what happens!**

