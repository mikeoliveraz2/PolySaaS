# Test OS Ticket with PolySniffer - Step by Step

## Goal
Verify PolySniffer is working by testing with OS Ticket (which we know works).

## Step 1: Start Django Server (if not running)
```bash
.\go.ps1
```
Wait for server to start on `http://localhost:8000`

## Step 2: Open PolySniffer Dashboard
1. Open browser: `http://localhost:8000/dose/polysniffer/`
2. Should see empty dashboard (no logs yet)
3. If you see errors, check Django server is running

## Step 3: Find OS Ticket Endpoint
1. Go to: `http://localhost:8000/admin/dose/passthroughendpoint/`
2. Look for OS Ticket endpoint in the list
3. You should see a **"🔍 Sniff"** button in the Debug column

## Step 4: Click "Sniff" Button
1. Click the **"🔍 Sniff"** button on OS Ticket endpoint
2. This should open PolySniffer interface (or redirect to dashboard)

## Step 5: Access OS Ticket
1. Go to: `http://localhost:8000/admin/osticket/`
2. Try to login (we know this works - 422 error is fixed!)
3. Navigate around the dashboard
4. Make a few requests (click links, load pages)

## Step 6: Check Captured Traffic
1. Go back to: `http://localhost:8000/dose/polysniffer/`
2. You should now see captured traffic! ✅
3. Look for:
   - GET requests to login.php
   - POST request to login.php (with ajax=1 parameter)
   - Status codes: 200 or 302 (success!)
   - Headers, cookies, POST data all visible

## Step 7: View Detailed Log
1. Click "View" on any log entry
2. See full request/response details
3. Check headers, cookies, POST data
4. Verify it matches what we fixed (ajax=1, proper headers, etc.)

## What You Should See

### Successful Login POST Request:
- **Method**: POST
- **Status**: 200 or 302 (not 422!)
- **Headers**:
  - `Content-Type: application/x-www-form-urlencoded; charset=UTF-8`
  - `X-Requested-With: XMLHttpRequest`
  - `Referer: https://oliverenterprises.app.saasify.cloud/scp/login.php`
- **POST Data**:
  - `__CSRFToken__`: (CSRF token)
  - `userid`: (username)
  - `passwd`: (password)
  - `do`: `scplogin`
  - `ajax`: `1` ✅ (this was the fix!)

## Expected Results

✅ **PolySniffer dashboard shows captured traffic**
✅ **Login POST shows status 200/302 (not 422)**
✅ **All headers present (Content-Type, X-Requested-With, etc.)**
✅ **POST data includes `ajax=1`**
✅ **Can view detailed logs**

## If Something Doesn't Work

- **Dashboard is empty?** - Traffic might not be captured yet, try accessing OS Ticket again
- **"Sniff" button doesn't work?** - Check browser console for errors
- **No traffic captured?** - Make sure you're actually accessing OS Ticket after clicking Sniff

## Next Steps After This Works

Once you confirm PolySniffer is capturing OS Ticket traffic correctly:
1. ✅ PolySniffer is working!
2. Ready to debug Notion
3. Ready to debug Airtable

**Start with Step 1 - open the PolySniffer dashboard!**

