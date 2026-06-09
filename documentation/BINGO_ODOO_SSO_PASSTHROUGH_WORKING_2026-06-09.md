# BINGO: Odoo SSO Passthrough Working

**Date:** 2026-06-09  
**Commit:** 5bf1ea96  
**Status:** ✅ VERIFIED WORKING

## What Was Achieved

Odoo now loads within the PolySaaS admin interface with full Single Sign-On (SSO) auto-login functionality. Users are automatically authenticated when accessing Odoo through the passthrough system, without seeing a login screen.

## The Problem

After the previous layout fix (BINGO 2026-06-09 earlier), Odoo was displaying correctly but SSO was broken:
1. Users saw the Odoo login screen instead of being auto-logged in
2. Manual login attempts resulted in `Forbidden (403) CSRF verification failed`
3. After fixes, navigation to `/odoo/apps` caused 404 errors
4. Session expired loops occurred

## Root Causes Identified

### 1. Tenant ID Bug
**Issue:** Code tried to access `tenant.id`, but the `Tenant` model uses `slug` as the primary key, not `id`.
```python
# WRONG:
tenant_id = tenant.id if tenant else None

# CORRECT:
tenant_id = tenant.pk if tenant else None
```
**Impact:** Credentials couldn't be retrieved from `TenantApp.extra_config`, so auto-login never ran.

### 2. Expired Session Cookie
**Issue:** Handler sent a cached `odoo_session_id` from `TenantApp.extra_config`, but this session had expired (from initial provisioning).
**Impact:** Odoo rejected the expired session, showing "Session Expired" dialog.

### 3. Missing URL Patterns
**Issue:** Odoo navigation generated URLs like `/odoo/apps` and `/apps` that weren't caught by the passthrough system.
**Impact:** 404 errors broke the user experience.

### 4. No Navigation Lock
**Issue:** JavaScript shim only intercepted `fetch()` and `XMLHttpRequest`, but not `window.location` assignments or `history.pushState/replaceState`.
**Impact:** When Odoo tried to navigate to `/apps`, it bypassed the proxy prefix, causing 404s and session loss.

## Solutions Implemented

### 1. Fixed Tenant Primary Key Access
**File:** `dose/passthrough/handlers/odoo_handler.py`
```python
# Line 66 - Changed from tenant.id to tenant.pk
tenant_id = tenant.pk if tenant else None  # Use .pk (primary key) instead of .id
```

### 2. Removed Expired Session Cookie Injection
**File:** `dose/passthrough/handlers/odoo_handler.py`
```python
def get_upstream_cookies(self, request):
    """Provide Odoo session cookie for SSO/auto-login."""
    # Always let client-side shim create a fresh session via auto-login
    # (cached session_id in extra_config is likely expired)
    print(f"[ODOO HANDLER] No upstream cookies - client will auto-login")
    return {}
```

### 3. Added URL Patterns for Orphaned Odoo Paths
**File:** `mysite/urls.py`

Added patterns to catch `/odoo/...` and `/apps` requests:
```python
# Catch /odoo/* paths (e.g., /odoo/apps, /odoo/settings, etc.)
path('odoo/', odoo_stray_web_request_view, {'rest': 'apps'}, name='odoo_apps_root'),
re_path(r'^odoo/(?P<rest>.*)$', odoo_stray_web_request_view, name='odoo_apps_subpath'),

# Catch bare /apps path (Odoo redirects here after login)
path('apps/', odoo_stray_web_request_view, {'rest': 'apps'}, name='odoo_bare_apps'),
```

### 4. Added Comprehensive Navigation Lock
**File:** `dose/passthrough/handlers/odoo_handler.py`

Added JavaScript to intercept all navigation attempts:
```javascript
// Navigation lock: intercept window.location assignments
Object.defineProperty(window, 'location', {
    set: function(val) {
        var rewritten = rewriteUrl(val);
        return _originalLocationSet.call(window, rewritten);
    }
});

// Intercept history.pushState and replaceState
history.pushState = function(state, title, url) {
    if (url) {
        var rewritten = rewriteUrl(url);
        return _originalPushState.call(this, state, title, rewritten);
    }
    return _originalPushState.call(this, state, title, url);
};
// (replaceState similar)
```

Also added `/apps` to the list of paths to rewrite:
```javascript
var ODOO_PATHS = ['/web', '/odoo', '/apps', '/report', '/download', '/api', '/base', '/bus'];
```

## Files Modified

1. **`dose/admin_views.py`**
   - Added `@csrf_exempt` decorator to `pt_admin_generic_passthrough_view` (defensive measure, CSRFExemptionMiddleware already handles it)
   - Added debug print to verify view execution

2. **`dose/passthrough/handlers/odoo_handler.py`**
   - Fixed `tenant.id` → `tenant.pk` bug in `_get_tenantapp_extra_config`
   - Removed expired session cookie logic in `get_upstream_cookies`
   - Added comprehensive navigation lock to `get_client_side_shim`
   - Added `/apps` to `ODOO_PATHS` list for URL rewriting
   - Used `json.dumps()` for safe credential escaping in JavaScript

3. **`mysite/urls.py`**
   - Added URL patterns for `/odoo/...` paths
   - Added URL pattern for `/apps` path

## How SSO Works Now

1. **User navigates to Odoo** via `/pt/admin/polysaas-odoo2.onrender.com/web`
2. **Handler retrieves credentials** from `TenantApp.extra_config` (using correct `tenant.pk`)
3. **Auto-login JavaScript injected** into page with credentials
4. **JavaScript executes** after page load:
   ```javascript
   fetch(PROXY_PREFIX + '/web/session/authenticate', {
       method: 'POST',
       body: JSON.stringify({
           jsonrpc: '2.0',
           method: 'call',
           params: { db, login, password }
       })
   })
   ```
5. **Odoo creates fresh session**, returns session cookie
6. **User is authenticated**, Odoo loads normally
7. **Navigation lock prevents** any navigation outside proxy prefix

## Verification Steps

✅ Tested on tenant: `polysaast132` (PolySaas Tst 132)  
✅ Odoo user: `pst132@you.com`  
✅ Auto-login successful without login screen  
✅ Odoo Apps page displays correctly  
✅ Navigation within Odoo works (no 404s)  
✅ No CSRF errors  
✅ No session expired loops  
✅ All network requests return 200 OK  

## Technical Notes

- The existing `CSRFExemptionMiddleware` already exempts all `/pt/...` paths from CSRF validation, so the `@csrf_exempt` decorator on the view is redundant but harmless
- The `TenantApp.extra_config` still contains an expired `odoo_session_id`, but it's no longer used
- The navigation lock intercepts client-side navigation; server-side redirects are handled by the URL patterns
- The auto-login uses credentials stored during tenant provisioning by `OdooTenantProvisioner`

## Related Documentation

- Previous BINGO: `BINGO_ODOO_PASSTHROUGH_LAYOUT_FIX_2026-06-09.md` (layout/CSS fix)
- SSO Architecture: `documentation/SSO-architecture.md` (if exists)
- Passthrough Handler Isolation: `.cursor/rules/passthrough-handler-isolation.mdc`

## Testing Checklist

- [x] Load Odoo through passthrough (`/pt/admin/polysaas-odoo2.onrender.com/web`)
- [x] Verify no login screen shown (auto-login works)
- [x] Verify Odoo Apps page loads correctly
- [x] Click various Odoo menu items
- [x] Verify no 404 errors in network tab
- [x] Verify no CSRF errors
- [x] Verify no session expired loops
- [x] Check browser console for `[ODOO SSO] Auto-login successful` message

---

**Certified Working:** 2026-06-09 12:36 PM (UTC+8)  
**Tested By:** Michael + Cursor Agent  
**Odoo Version:** polysaas-odoo2.onrender.com  
**Database:** polysaas_odoo
