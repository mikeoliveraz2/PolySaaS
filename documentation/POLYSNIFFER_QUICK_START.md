# PolySniffer Quick Start Guide

## Current Status

✅ **OS Ticket is configured** - 2 endpoints found in database
- Endpoint 1: `osticket` → `https://oliverenterprises.app.saasify.cloud/scp/`
- Endpoint 2: `/admin/osticket/` → `https://oliverenterprises.app.saasify.cloud/scp/dashboard.php`

⚠️ **Issue**: Getting HTTP 422 when accessing OS ticket (but still receiving HTML)

## Using PolySniffer to Debug

### Option 1: Live Demo (Fastest - No Installation)

1. **Open PolySniffer**: https://polysniffer.up.railway.app

2. **Enter OS Ticket URL**:
   ```
   https://oliverenterprises.app.saasify.cloud/scp/login.php
   ```

3. **Paste Cookies** (optional - if you have them):
   - Open browser DevTools (F12)
   - Go to Application → Cookies → `oliverenterprises.app.saasify.cloud`
   - Copy cookie values
   - Paste into PolySniffer cookie field

4. **Navigate through login**:
   - Load the login page
   - Enter your credentials
   - Click login
   - Navigate to dashboard

5. **Export HAR file**:
   - Click "Export HAR" button
   - Save the file

6. **Compare with our proxy**:
   - Run: `python test_osticket_with_polysniffer.py`
   - Compare headers, cookies, POST data

### Option 2: Self-Hosted (Docker - Requires Docker Desktop)

If you install Docker Desktop:

```bash
git clone https://github.com/oliver-oliver/PolySniffer.git
cd PolySniffer
docker compose up -d
```

Access at: http://localhost:3000

## What to Look For

When comparing PolySniffer HAR with our proxy:

1. **Request Headers**:
   - `Content-Type`
   - `X-Requested-With`
   - `Referer`
   - `User-Agent`
   - `Accept` headers

2. **Cookies**:
   - `OSTSESSID` value
   - `__CSRFToken__` value
   - Cookie domain/path settings

3. **POST Data**:
   - All form fields
   - CSRF token field name (`__CSRFToken__` vs `token`)
   - Hidden fields
   - `ajax=1` parameter (if present)

4. **Response**:
   - Status code (should be 200 or 302, not 422)
   - Set-Cookie headers
   - Redirect location

## Quick Test Commands

```bash
# Test what our proxy sends
python test_osticket_with_polysniffer.py

# Full login cycle test
python test_osticket_full_cycle.py

# Check current configuration
python check_osticket_status.py
```

## Access URLs

- Django Admin: http://localhost:8000/admin/osticket/
- Passthrough Route: http://localhost:8000/pt/admin/osticket/

## Next Steps After PolySniffer

1. Capture working login flow in PolySniffer
2. Export HAR file
3. Compare with `test_osticket_with_polysniffer.py` output
4. Identify differences (likely missing headers or wrong cookie format)
5. Update `dose/osticket_admin.py` to match real browser behavior
6. Test again

