# PolySniffer Next Steps - Debug Notion & Airtable

## 🎯 Goal
Use PolySniffer to debug Notion and Airtable passthrough endpoints, just like we did for OS Ticket!

## Step 1: Verify PolySniffer is Working

### 1.1 Check Dashboard
- Go to: `/dose/polysniffer/`
- Should show empty dashboard (no logs yet)
- If you see errors, check Django server is running

### 1.2 Test with OS Ticket (Known Working)
1. Go to Django Admin → PassThroughEndpoint
2. Find OS Ticket endpoint
3. Click "🔍 Sniff" button
4. This should open PolySniffer interface
5. Try accessing OS Ticket through it
6. Check `/dose/polysniffer/` dashboard - you should see captured traffic!

## Step 2: Fix olient Schema (If Needed)

If TrafficLog table is missing in olient schema:
```bash
# We can manually create it or fix the contenttypes issue
# Let me know if you want me to fix this now
```

## Step 3: Debug Notion

### 3.1 Find Notion Endpoint
1. Django Admin → PassThroughEndpoint
2. Find Notion endpoint (or create one if missing)
3. Note the endpoint URL

### 3.2 Use PolySniffer
1. Click "🔍 Sniff" on Notion endpoint
2. PolySniffer opens with Notion URL pre-filled
3. Try to access Notion through PolySniffer
4. Navigate around, try to login/create content
5. Watch the traffic being captured

### 3.3 Analyze Captured Traffic
1. Go to `/dose/polysniffer/` dashboard
2. Filter by endpoint = "Notion"
3. Look for:
   - **Failed requests** (4xx/5xx status codes)
   - **Missing headers** (compare with working requests)
   - **Cookie issues** (session not maintained)
   - **POST data format** (wrong structure?)

### 3.4 Compare with Working Example
- Compare Notion requests with OS Ticket requests
- Look for differences in:
  - Headers (Content-Type, Authorization, etc.)
  - Cookies (session management)
  - Request format (JSON vs form-data)

## Step 4: Debug Airtable

### 4.1 Find Airtable Endpoint
1. Django Admin → PassThroughEndpoint
2. Find Airtable endpoint
3. Note the endpoint URL

### 4.2 Use PolySniffer
1. Click "🔍 Sniff" on Airtable endpoint
2. Try to access Airtable through PolySniffer
3. Capture traffic

### 4.3 Analyze Issues
- Check for authentication problems
- Look for API key issues
- Check request format

## Step 5: Apply Fixes

Based on PolySniffer findings:

### For Notion:
- Update passthrough view to match real browser behavior
- Fix headers if missing
- Fix cookie handling if broken
- Fix POST data format if wrong

### For Airtable:
- Check API authentication
- Verify request format
- Fix any missing parameters

## Quick Reference

### PolySniffer URLs
- **Dashboard**: `/dose/polysniffer/`
- **Admin**: Django Admin → Traffic Logs
- **Sniff Button**: Django Admin → PassThroughEndpoint → "🔍 Sniff"

### What to Look For
1. **Status Codes**: 200/302 = good, 4xx/5xx = problem
2. **Headers**: Missing required headers?
3. **Cookies**: Session not maintained?
4. **POST Data**: Wrong format or missing fields?
5. **Response**: What does the server actually return?

### Export HAR Files
- Click "HAR" button on any log entry
- Import into Chrome DevTools for detailed analysis
- Compare with working requests

## Expected Results

After debugging with PolySniffer:
- ✅ Notion passthrough working
- ✅ Airtable passthrough working
- ✅ All traffic logged in database
- ✅ Easy to debug future issues

## Files to Check

If Notion/Airtable have issues, we'll likely update:
- `dose/generic_passthrough_views.py` - Main passthrough logic
- `dose/passthrough_views.py` - Service-specific handlers
- Or create dedicated views like `osticket_admin.py`

Let's get Notion and Airtable working! 🚀

