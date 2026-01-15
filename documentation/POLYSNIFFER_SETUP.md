# PolySniffer - HTTP MITM Logger Setup Guide

## Overview

PolySniffer is a Man-in-the-Middle proxy that logs **every single request and response** between your browser and external services. This is the ultimate debugging tool for passthrough integrations.

## Why We Need This

When building passthrough proxies, we need to know:
- **What headers** the real browser sends
- **What cookies** are required
- **What request format** the service expects
- **What WebSocket endpoints** are used
- **What hidden API calls** the frontend makes

PolySniffer captures all of this automatically.

## Quick Start

### Option 1: Use Live Demo (Fastest)

**URL:** https://polysniffer.up.railway.app

1. Open the URL in your browser
2. Paste the target URL (e.g., `https://oliverenterprises.app.saasify.cloud/scp/login.php`)
3. Paste your cookies (or login inside PolySniffer)
4. Click around the app for 2-5 minutes
5. Export HAR file
6. Compare with what our proxy sends

### Option 2: Self-Hosted (Docker)

```bash
git clone https://github.com/oliver-oliver/PolySniffer.git
cd PolySniffer
docker compose up -d
```

Access at: http://localhost:3000

### Option 3: Deploy to Railway (Permanent)

**One-click deploy:** https://railway.app/template/polysniffer?referralCode=oliver

## How to Use for OSTicket Debugging

### Step 1: Capture Real Browser Behavior

1. Open PolySniffer (live demo or self-hosted)
2. Enter OSTicket URL: `https://oliverenterprises.app.saasify.cloud/scp/login.php`
3. Paste your OSTicket cookies (from browser DevTools)
4. Navigate through the login flow:
   - Load login page
   - Enter credentials
   - Click login
   - Navigate to dashboard
5. Export HAR file

### Step 2: Compare with Our Proxy

1. Run our full cycle test:
   ```bash
   python test_osticket_full_cycle.py
   ```
2. Compare the HAR export with our test output
3. Look for differences in:
   - Request headers
   - Cookie values
   - POST data format
   - Response handling

### Step 3: Fix Missing Pieces

Based on the comparison, update our proxy to match the real browser behavior.

## Features

- **Full HAR Export** - Import directly into Chrome DevTools
- **Live Request/Response Viewer** - See everything in real-time
- **WebSocket Logging** - Capture WebSocket frames
- **Cookie Jar Sync** - Paste cookies once, stays logged in
- **Replay Mode** - Send exact same requests from our proxy
- **Search/Filter** - By domain, method, status code
- **Dark Mode** - Easy on the eyes

## Integration with PolySaaS

Future enhancement: Add "Launch Sniffer" button directly in PolySaaS sidebar that:
1. Opens PolySniffer in new window
2. Pre-fills current passthrough endpoint URL
3. Pre-loads cookies from current session
4. One-click → instant debugging

## Example Workflow

### Debugging OSTicket "Access Denied"

1. **Capture Real Browser:**
   ```
   PolySniffer → OSTicket login → Export HAR
   ```

2. **Capture Our Proxy:**
   ```
   python test_osticket_full_cycle.py → Save output
   ```

3. **Compare:**
   - Real browser POST headers vs our POST headers
   - Real browser cookies vs our session cookies
   - Real browser POST data vs our POST data

4. **Find the Difference:**
   - Missing header? → Add it
   - Wrong cookie value? → Fix session sync
   - Wrong POST format? → Fix data serialization

5. **Test Again:**
   - Run test → Should match real browser now

## Files

- `test_osticket_full_cycle.py` - Full GET → POST cycle test
- `test_osticket_rewriting.py` - TDD tests for rewriting logic
- `documentation/POLYSNIFFER_SETUP.md` - This file

## Next Steps

After demo video:
1. Set up PolySniffer (self-hosted or Railway)
2. Capture OSTicket login flow
3. Compare with our proxy
4. Fix any differences
5. Verify login works

## Resources

- **Live Demo:** https://polysniffer.up.railway.app
- **GitHub Repo:** https://github.com/oliver-oliver/PolySniffer
- **Railway Deploy:** https://railway.app/template/polysniffer?referralCode=oliver

