# PolySniffer OSTicket 422 Debugging Guide

## Quick 2-Minute Diagnosis

### Step 1: Capture Working Request
1. Open PolySniffer: https://polysniffer.up.railway.app
2. Enter OSTicket URL: `https://oliverenterprises.app.saasify.cloud/scp/login.php`
3. Paste cookies from your browser (DevTools → Application → Cookies → Copy all)
4. **Manually login** with your real credentials inside PolySniffer
5. Export HAR file

### Step 2: Compare with Our Proxy
1. Check terminal logs for `[OSTICKET POST]` messages
2. Compare:
   - **Headers**: Content-Type, X-Requested-With, Referer
   - **Cookies**: OSTSESSID, __CSRFToken__, csrf_token
   - **POST Data**: All form fields, especially `ajax=1` parameter

### Step 3: Find the Missing Piece

## Top 5 Causes of 422 (in order of likelihood)

### 1. Missing/Wrong CSRF Token ⚠️ MOST LIKELY
**How to confirm:** Check PolySniffer HAR → POST request → form data → look for `__CSRFToken__` or `token` field

**Our current code:**
- ✅ We extract CSRF token from GET response
- ✅ We include it in POST data
- ❓ **Issue**: Token might be from different session than POST request

**Fix:** Ensure CSRF token is from the SAME session that makes the POST request

### 2. Cookie Jar Not Sent Properly ⚠️ SECOND MOST LIKELY
**How to confirm:** Compare cookies in PolySniffer HAR vs our session cookies

**Our current code:**
- ✅ We sync browser cookies to session
- ❓ **Issue**: Might be missing some cookies or wrong domain/path

**Fix:** Forward ALL cookies bidirectionally, ensure domain/path match

### 3. Wrong Content-Type or Missing Headers
**How to confirm:** Check PolySniffer HAR → POST request → Headers

**Our current code:**
- ✅ We set `Content-Type: application/x-www-form-urlencoded`
- ✅ We detect AJAX and set `X-Requested-With: XMLHttpRequest`
- ❓ **Issue**: Might need additional headers

**Fix:** Match exact headers from PolySniffer HAR

### 4. Missing Hidden Fields
**How to confirm:** Check PolySniffer HAR → POST request → form data → look for hidden fields

**Our current code:**
- ❌ We only send visible form fields
- ❓ **Issue**: OSTicket might add hidden fields via JavaScript

**Fix:** Use Playwright to render page fully, then submit (handles this automatically)

### 5. Cloudflare/Bot Detection
**How to confirm:** Check if OSTicket uses Cloudflare (look for `cf-` headers in PolySniffer)

**Our current code:**
- ❌ We use raw requests (looks like a bot)
- **Fix:** Use Playwright (looks like a real browser)

## Quick Fix: Playwright Login (Bypasses All Issues)

If PolySniffer shows complex requirements, use the Playwright-based login:

```python
from dose.services.osticket_playwright_login import osticket_login_sync

# In your POST handler:
result = osticket_login_sync(
    login_url="https://oliverenterprises.app.saasify.cloud/scp/login.php",
    username=request.POST.get('userid'),
    password=request.POST.get('passwd'),
    cookies=request.COOKIES  # Pass browser cookies
)

if result['success']:
    # Save cookies to session
    for cookie in result['cookies']:
        session.cookies.set(cookie['name'], cookie['value'])
    # Redirect to result['redirect_url']
```

This handles:
- ✅ CSRF tokens automatically
- ✅ All cookies automatically
- ✅ Hidden fields automatically
- ✅ Bot detection (looks like real browser)

## What to Look For in PolySniffer HAR

1. **POST Request to `login.php`**:
   - Headers section → Compare with our `headers` dict
   - Cookies section → Compare with our `session.cookies`
   - Form Data section → Compare with our `post_data`

2. **GET Request to `login.php`** (before POST):
   - Response → HTML → Find `<input name="__CSRFToken__">` → Compare value with what we extract

3. **Set-Cookie Headers**:
   - From GET response → Compare with what we save to browser
   - From POST response → Compare with what we save to browser

## Next Steps

1. ✅ Run PolySniffer capture (2 minutes)
2. ✅ Export HAR file
3. ✅ Compare POST request with our proxy logs
4. ✅ Identify missing piece (likely #1 or #2)
5. ✅ Apply fix
6. ✅ Test login again

## Files

- `dose/services/osticket_playwright_login.py` - Playwright-based login (bypasses all 422 issues)
- `test_osticket_full_cycle.py` - Full cycle test (compare with PolySniffer)
- `documentation/POLYSNIFFER_SETUP.md` - PolySniffer setup guide

