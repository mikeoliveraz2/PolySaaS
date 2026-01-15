# Quick Alternative: Use Chrome DevTools (No Setup Needed!)

Since Railway template is giving 404, here's the **fastest way** to capture OS ticket requests:

## Step 1: Open Chrome DevTools
1. Open Chrome browser
2. Press **F12** (or right-click → "Inspect")
3. Click the **"Network"** tab

## Step 2: Navigate to OS Ticket
1. In the address bar, go to: `https://oliverenterprises.app.saasify.cloud/scp/login.php`
2. You'll see requests appearing in the Network tab

## Step 3: Login
1. Enter your OS ticket username and password
2. Click "Login"
3. Navigate around the dashboard

## Step 4: Capture Requests
1. In the Network tab, you'll see all HTTP requests
2. Find the **POST request to `login.php`**
3. Click on it to see:
   - **Headers** tab → Request Headers (Content-Type, Referer, etc.)
   - **Payload** tab → Form Data (userid, passwd, __CSRFToken__, etc.)
   - **Cookies** tab → All cookies sent

## Step 5: Save as HAR
1. Right-click anywhere in the Network tab
2. Select **"Save all as HAR with content"**
3. Save the file (e.g., `osticket_login.har`)

## Step 6: Compare with Our Proxy
Run this in terminal:
```bash
python test_osticket_with_polysniffer.py
```

Then compare:
- **Headers** from DevTools vs our proxy
- **Cookies** from DevTools vs our proxy
- **POST data** from DevTools vs our proxy

## What to Look For

In Chrome DevTools, when you click on the POST request to `login.php`:

### Headers Tab
- `Content-Type: application/x-www-form-urlencoded`
- `Referer: https://oliverenterprises.app.saasify.cloud/scp/login.php`
- `Cookie: OSTSESSID=...; __CSRFToken__=...`

### Payload Tab (Form Data)
- `__CSRFToken__`: (the CSRF token value)
- `userid`: (your username)
- `passwd`: (your password)
- `do`: `scplogin`

### Response Tab
- Status: Should be **200** or **302** (not 422!)
- Headers: Check `Set-Cookie` headers
- Preview: Should show redirect or success page

## Compare with Our Proxy

Our proxy is getting **422** status. Compare what DevTools shows vs what our proxy sends to find the difference!

---

**This is actually easier than PolySniffer** - no setup needed, works immediately! 🚀

