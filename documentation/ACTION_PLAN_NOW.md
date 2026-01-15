# Action Plan - Test PolySniffer & Debug Notion/Airtable

## Step 1: Verify PolySniffer is Working (2 minutes)

### 1.1 Check Dashboard
1. Make sure Django server is running (`.\go.ps1` if needed)
2. Open browser: `http://localhost:8000/dose/polysniffer/`
3. Should see empty dashboard (no logs yet) ✅

### 1.2 Test with OS Ticket (Known Working)
1. Go to: `http://localhost:8000/admin/dose/passthroughendpoint/`
2. Find OS Ticket endpoint in the list
3. Click the **"🔍 Sniff"** button
4. PolySniffer should open (or redirect to dashboard)
5. Try accessing OS Ticket through it
6. Go back to `/dose/polysniffer/` dashboard
7. You should see captured traffic! ✅

**If this works, PolySniffer is ready!**

## Step 2: Debug Notion (5-10 minutes)

### 2.1 Check Notion Endpoint
1. In Django Admin → PassThroughEndpoint
2. Look for Notion endpoint
3. If missing, create one:
   - Trigger Path: `/admin/notion/` or `/notion/`
   - Endpoint URL: `https://www.notion.so/`
   - Passthrough Type: `scraper`
   - Enabled: ✓

### 2.2 Use PolySniffer on Notion
1. Click **"🔍 Sniff"** on Notion endpoint
2. Try to access Notion through PolySniffer
3. Navigate around, try to login/create content
4. Watch for errors or issues

### 2.3 Analyze Captured Traffic
1. Go to `/dose/polysniffer/` dashboard
2. Filter by endpoint = "Notion" (or whatever name you used)
3. Look for:
   - ❌ **Failed requests** (4xx/5xx status codes)
   - ❌ **Missing headers** (compare with OS Ticket)
   - ❌ **Cookie issues** (session not maintained)
   - ❌ **POST data format** (wrong structure?)

### 2.4 Compare with OS Ticket
1. Filter dashboard to show OS Ticket requests
2. Compare headers, cookies, POST data
3. Note the differences
4. These differences are likely the problem!

## Step 3: Debug Airtable (5-10 minutes)

### 3.1 Check Airtable Endpoint
1. Django Admin → PassThroughEndpoint
2. Find Airtable endpoint
3. If missing, create one:
   - Trigger Path: `/admin/airtable/` or `/airtable/`
   - Endpoint URL: `https://airtable.com/`
   - Passthrough Type: `scraper`
   - Enabled: ✓

### 3.2 Use PolySniffer on Airtable
1. Click **"🔍 Sniff"** on Airtable endpoint
2. Try to access Airtable
3. Capture traffic

### 3.3 Analyze Issues
- Check for authentication problems
- Look for API key issues
- Check request format

## Step 4: Report Findings

After testing, tell me:
1. **What errors you see** in PolySniffer dashboard
2. **What's different** between Notion/Airtable and OS Ticket
3. **What status codes** you're getting (422? 403? 500?)

Then I can help fix the issues!

## Quick Reference

### URLs
- **PolySniffer Dashboard**: `/dose/polysniffer/`
- **Admin**: Django Admin → Traffic Logs
- **PassThroughEndpoint Admin**: `/admin/dose/passthroughendpoint/`

### What to Look For
- Status codes: 200/302 = good, 4xx/5xx = problem
- Headers: Missing required headers?
- Cookies: Session not maintained?
- POST Data: Wrong format or missing fields?

## Expected Outcome

After this process:
- ✅ Know exactly what's wrong with Notion/Airtable
- ✅ Have captured traffic to compare
- ✅ Ready to apply fixes based on real data

**Start with Step 1 - verify PolySniffer works with OS Ticket first!**

