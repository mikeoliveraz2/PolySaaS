# OSTicket 422 Error - Systematic Research & Fix Plan

## The Problem
Django view at `/admin/osticket/` is getting HTTP 422 from endpoint, but Flask proxy on port 8001 works.

## Key Questions to Answer

### 1. Is the Flask Proxy Also Getting 422?
The Flask proxy works, but does it ALSO get 422 and just handle it gracefully?

**To test:**
```powershell
# Start Flask proxy
python -m flask --app dose.interactive_proxy_flask run --port 8001

# In another terminal, test it
python -c "import requests; r = requests.get('http://127.0.0.1:8001/admin/osticket/login.php', verify=False); print(f'Status: {r.status_code}'); print(r.text[:200])"
```

**Expected finding:**
- If Flask gets 200: The endpoint is fine, issue is Django view
- If Flask gets 422: The endpoint itself returns 422 (Django view is correct too)

### 2. What Is the 422 Response?
Is it HTML error page, JSON, or plain text?

**To investigate:**
Run `deep_research_422.py` to see:
- Response headers
- Response body
- Content-Type
- Redirects
- Form fields

### 3. What's Different Between Requests?

**Flask Proxy approach:**
```python
sess = requests.Session()
resp = sess.get(target_url, timeout=15, allow_redirects=True)
```

**Django View approach:**
```python
sess = requests.Session()
headers = {
    'User-Agent': '...',
    'Accept': '...',
    ...
}
response = sess.get(target_url, headers=headers, timeout=15, verify=False)
```

Differences:
- `verify=False` (but Flask doesn't have this either)
- Extra headers (Flask doesn't send these)
- Different User-Agent

## Systematic Fix Plan

### Step 1: Run Deep Research
```powershell
python deep_research_422.py
```

This will show us:
- ✓ Which paths return what status codes
- ✓ What the 422 response actually contains
- ✓ If there are redirects
- ✓ CSRF tokens or other requirements

### Step 2: Simplify Request to Match Flask
If Flask proxy gets 200 and our view gets 422, match their exact approach:

```python
# Current Django approach (might get 422)
headers = {...lots of headers...}
response = sess.get(target_url, headers=headers, timeout=15, verify=False)

# Flask approach (known to work)
response = sess.get(target_url, timeout=15)  # Fewer headers
```

**Action:** Remove extra headers one by one and test.

### Step 3: Check for Required Cookies/Auth
OSTicket might require:
- Initial page fetch to set cookies
- Login before accessing other pages

**Fix approach:**
```python
# Fetch initial page first to get cookies
r1 = sess.get(f"{REAL_BASE}login.php", timeout=15)

# Then make actual request
r2 = sess.get(target_url, timeout=15)
```

### Step 4: Follow Redirects Properly
Maybe the endpoint redirects and our view isn't handling it right.

**Check:**
```python
print(f"Final URL after redirects: {response.url}")
print(f"Request history: {[r.status_code for r in response.history]}")
```

### Step 5: Handle 422 Gracefully
If 422 is expected from OSTicket, display it anyway (like Flask proxy does).

**Current code already does this,** but make sure:
```python
if response.status_code >= 400:
    # Show the error page anyway
    if 'html' in content_type or response.text.startswith('<'):
        doseified = doseify_html(response.text)
        # Display wrapped in admin template
```

## Research Scripts

All scripts are in the workspace root:

1. **research_422.py** - Basic tests with different approaches
2. **deep_research_422.py** - Detailed analysis with redirects, forms, CSRF tokens
3. **test_flask_vs_direct.py** - Compares Flask proxy vs direct endpoint

## Running the Research

```powershell
# Terminal 1: Start Django
python manage.py runserver 8000

# Terminal 2: Start Flask proxy (optional, for comparison)
python -m flask --app dose.interactive_proxy_flask run --port 8001

# Terminal 3: Run diagnostics
python deep_research_422.py
```

## Expected Outcomes

### Scenario 1: Flask Gets 200, Django Gets 422
**Issue:** Django view is making the request differently

**Fix:** Simplify request to match Flask
```python
# Remove extra headers
# Test with minimal User-Agent
# Match Flask's Session creation exactly
```

### Scenario 2: Both Get 422
**Issue:** OSTicket endpoint returns 422 for this path

**Fix:** Use different path
```python
# Try /dashboard.php instead of /login.php
# Try /index.php
# Try just /scp/ (might redirect)
```

### Scenario 3: Flask Gets 422 But Displays, Django Shows Error
**Issue:** Code is correct, just need to display 422 response

**Fix:** Already implemented - make sure it's rendering properly
```python
# Ensure 422 response HTML is being doseified
# Check error template is showing full response
```

## Success Criteria

✅ When fixed:
1. Visit `/admin/osticket/`
2. See OSTicket login page or dashboard
3. Page displays in admin interface (not fullscreen)
4. Sidebar navigation works (AJAX interception)
5. Forms submit properly
6. Session persists across requests

## Key Files

- `dose/osticket_admin.py` - Main view (has enhanced logging)
- `templates/admin/osticket_error.html` - Error display
- `dose/interactive_proxy_flask.py` - Reference implementation (working)
- Research scripts: `research_422.py`, `deep_research_422.py`, `test_flask_vs_direct.py`
