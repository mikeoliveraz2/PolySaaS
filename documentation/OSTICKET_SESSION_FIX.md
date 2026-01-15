# OSTicket Passthrough Session Persistence Fix

## Problem
After implementing the OSTicket login form in the Django admin, users could see the form but login was not working. The form would submit but the session was not being maintained for subsequent requests, causing the user to be logged out immediately.

## Root Causes

### 1. No Session/Cookie Persistence
**Issue**: Each request to `/admin/passthrough/osticket/` was creating a new `requests` connection without maintaining cookies from the OSTicket server.

**Impact**:
- User submits login with credentials
- OSTicket returns Set-Cookie header with session cookie
- Cookie is lost because we're not storing it
- Next request has no authentication

### 2. Missing POST Redirect Handling
**Issue**: OSTicket's login POST redirects to dashboard (HTTP 302), but code wasn't following the redirect to get the authenticated page.

**Impact**: Form POST succeeds but user sees redirect page, not dashboard.

## Solution

### 1. Implement Session Persistence with `requests.Session()`

**File**: `dose/passthrough_views.py`

**Changes in `generic_html_passthrough()` function**:

```python
# Create a session object to persist cookies
session = requests.Session()

# Restore any previously saved cookies from Django session
service_cookies_key = f"_passthrough_cookies_{service_name.lower()}"
if service_cookies_key in request.session:
    logger.info(f"Restoring saved cookies for {service_name}")
    saved_cookies = request.session[service_cookies_key]
    for cookie_dict in saved_cookies:
        session.cookies.set(
            name=cookie_dict['name'],
            value=cookie_dict['value'],
            domain=cookie_dict.get('domain', ''),
            path=cookie_dict.get('path', '/'),
        )
```

**Key Points**:
- Use `requests.Session()` object instead of individual `requests.post()` calls
- Session object persists cookies automatically within the same request lifecycle
- After each request, save cookies back to Django's session storage
- On subsequent requests, restore cookies from Django session before making the request

### 2. Save Cookies to Django Session for Multi-Request Persistence

```python
# Save any new cookies back to Django session
if len(session.cookies) > 0:
    logger.info(f"Saving {len(session.cookies)} cookies to Django session")
    cookies_to_save = []
    for cookie in session.cookies:
        cookies_to_save.append({
            'name': cookie.name,
            'value': cookie.value,
            'domain': cookie.domain,
            'path': cookie.path,
        })
    request.session[service_cookies_key] = cookies_to_save
    request.session.modified = True
```

**Why Django session?**
- Django session is per-user and request-scoped
- Each user maintains their own OSTicket session
- Session persists across multiple passthrough requests
- Session is automatically cleaned up when user logs out

### 3. Handle POST Redirects (Login Flow)

```python
# Handle redirects for POST requests (common after login)
if request.method == 'POST' and response.status_code in [301, 302, 303, 307, 308]:
    redirect_url = response.headers.get('Location', '')
    logger.info(f"POST request resulted in redirect: {response.status_code} to {redirect_url}")

    if redirect_url:
        # Extract and rewrite redirect to proxy path
        from urllib.parse import urlparse
        parsed = urlparse(redirect_url)
        redirect_path = parsed.path

        # If it's redirecting to the same domain, rewrite to proxy path
        if parsed.netloc == urlparse(real_domain).netloc or not parsed.netloc:
            # Build new path and follow redirect
            redirect_response = session.get(
                real_domain + redirect_path if redirect_path.startswith('/') else real_domain + '/' + redirect_path,
                timeout=10,
                verify=False
            )
            response = redirect_response
```

**Why this matters**:
- OSTicket login POST redirects to dashboard or profile page
- Without following redirect, user sees redirect response (usually empty)
- Following redirect with maintained session returns the authenticated page

## Data Flow

### Login Sequence with Fix

1. **Request 1**: User loads `/admin/passthrough/osticket/`
   - No cookies in Django session
   - Create new `requests.Session()`
   - GET request to OSTicket login form
   - Response has Set-Cookie in headers
   - Save cookies to Django session: `_passthrough_cookies_osticket`

2. **Request 2**: User submits login form to `/admin/passthrough/osticket/login.php`
   - Restore cookies from Django session to `requests.Session()`
   - POST credentials with restored cookies
   - OSTicket accepts auth, returns 302 redirect to dashboard
   - We follow the redirect with maintained session
   - Dashboard HTML returned to user (now authenticated)
   - Updated cookies saved back to Django session

3. **Request 3+**: User navigates to `/admin/passthrough/osticket/dashboard.php`
   - Restore cookies from Django session
   - All requests maintain authentication

## Technical Details

### Session Storage Key
```python
service_cookies_key = f"_passthrough_cookies_{service_name.lower()}"
# Example: "_passthrough_cookies_osticket"
```

### Cookie Format
```python
{
    'name': 'OSTICKET_SESSION_ID',
    'value': 'abc123xyz789',
    'domain': 'oliverenterprises.app.saasify.cloud',
    'path': '/scp/'
}
```

### Redirect Detection
Handles all standard HTTP redirect codes:
- 301: Moved Permanently
- 302: Found (most common for form submission)
- 303: See Other
- 307: Temporary Redirect
- 308: Permanent Redirect

## Testing the Fix

### Manual Test Steps

1. **Navigate to OSTicket in Admin**
   - Go to Django admin
   - Click OSTicket link
   - Login form should load

2. **Submit Login**
   - Enter valid OSTicket credentials
   - Click login button
   - Should be redirected to dashboard (not login page again)
   - Dashboard content should display

3. **Verify Multi-Page Navigation**
   - Click links on dashboard
   - Should maintain authentication across pages
   - No 403 errors or redirects to login

4. **Check Logs**
   - Look for "Saving X cookies to Django session"
   - Look for "Restoring saved cookies"
   - Look for successful redirect handling

### Debug Mode

Add debug logging to verify cookie handling:

```python
# In passthrough_views.py, look for:
# "Restoring saved cookies for" - Cookie restoration
# "Saving ... cookies to Django session" - Cookie persistence
# "Rewritten redirect" - Redirect handling
```

## Files Modified

- `dose/passthrough_views.py` - `generic_html_passthrough()` function
  - Lines 315-395: Session persistence logic
  - Lines 398-425: Redirect handling
  - Lines 428+: Unchanged HTML rewriting and CSRF injection

## Backward Compatibility

- All changes are additive (no breaking changes)
- Existing Gmail passthrough not affected
- New session persistence is transparent to other services
- Falls back gracefully if no cookies are present

## Future Improvements

1. **Session Timeout**: Add expiration time to saved cookies
2. **Cookie Encryption**: Encrypt sensitive cookies in Django session
3. **Multi-tab Support**: Store per-tab session ID instead of global
4. **Automatic Re-auth**: Detect 401/403 and prompt for re-login
5. **Session Debugging UI**: Dashboard showing active sessions per service

## Related Files

- `mysite/external_passthrough_middleware.py` - Middleware bypass for passthrough paths
- `templates/admin/passthrough.html` - Admin template wrapper
- `mysite/urls.py` - Passthrough URL routing
- `dose/passthrough_views.py` - All passthrough logic
