<!-- SUPERSEDED — see AI_RULES.md section 3 -->

> **SUPERSEDED (2026-09-01).** The direct upstream asset hotlinking recommended
> below contradicts `AI_RULES.md` section 3. Assets are served through the
> passthrough, not hotlinked from the upstream origin.
> Retained for historical context — do not implement from this document.

# Correct Asset Loading Architecture

## Flow Diagram

```
1. User requests /admin/osticket/
   ↓
2. Django view fetches https://oliverenterprises.app.saasify.cloud/
   ↓
3. OSTicket returns HTML with:
   - <link href="css/login.css">
   - <script src="js/script.js">
   ↓
4. doseify_html() rewrites asset paths:
   - css/login.css → https://oliverenterprises.app.saasify.cloud/css/login.css
   - js/script.js → https://oliverenterprises.app.saasify.cloud/js/script.js
   ↓
5. Django returns HTML to browser
   ↓
6. Browser parses HTML and sees:
   - <link href="https://oliverenterprises.app.saasify.cloud/css/login.css">
   - <script src="https://oliverenterprises.app.saasify.cloud/js/script.js">
   ↓
7. Browser fetches CSS/JS DIRECTLY from https://oliverenterprises.app.saasify.cloud/
   (NOT through Django proxy)
   ↓
8. If CSS/JS contains URLs, those might need rewriting
   (e.g., background-image: url('images/bg.png'))
   (e.g., import from './utils.js')
   But OSTicket should handle relative paths correctly
```

## Key Points

### ✅ Correct Approach
1. **HTML processing**: Goes through Django view (/admin/osticket/)
2. **Asset references in HTML**: Rewritten to full external domain
3. **CSS/JS files themselves**: Fetched directly from external host
4. **If CSS has URLs**: Should use absolute paths or relative paths that work from OSTicket's host

### ❌ Wrong Approach (What I was doing)
1. Routing `/admin/osticket/css/login.css` requests through proxy
2. This creates unnecessary overhead
3. Defeats the purpose of CDN/static hosting

## Code Changes Needed

### In doseify_html():
```python
# Relative assets - prepend FULL external domain
css/login.css → https://oliverenterprises.app.saasify.cloud/css/login.css ✅

# Absolute assets - prepend full external domain
/css/login.css → https://oliverenterprises.app.saasify.cloud/css/login.css ✅
```

### In view (osticket_admin_view):
```python
# Only process HTML requests
# CSS/JS requests shouldn't even reach here because:
# 1. They have .css/.js extensions in the path
# 2. We want them to go directly to OSTicket, not through proxy

# BUT if they do come through (nested resources), return them as-is
if is_asset:
    return HttpResponse(response.content, content_type=content_type)
```

## CORS Headers

If browser complains about CORS when loading from direct domain, might need:
- OSTicket to have CORS headers enabled
- OR fetch through proxy (secondary fallback)
- OR set proper headers when forwarding through proxy

Currently leaving at OSTicket level to handle.

## Exception: When Assets Need Proxy

If asset URLs inside CSS/JS reference other paths:
```css
/* In style.css from OSTicket */
background-image: url('./images/bg.png');
/* This is relative to the CSS file location, works fine directly */

background-image: url('/images/bg.png');
/* This is absolute, works fine directly */

background-image: url('https://other-service.com/image.png');
/* This references external service, works fine directly */
```

All of these work fine when CSS is loaded directly from OSTicket. Only issue is if CSS references relative paths that don't work from their host, which would be a bug in OSTicket itself.

## Summary

✅ **Current Fix Status**:
- HTML is processed through Django
- Asset paths in HTML are rewritten to full external domain
- Browser fetches CSS/JS directly from external host
- View returns assets as-is if they accidentally come through proxy
- No unnecessary proxying of static assets

**Result**: Faster loading, cleaner architecture, CSS/JS work correctly!
