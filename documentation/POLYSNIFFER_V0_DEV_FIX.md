# PolySniffer v0.dev Proxy Fix - Complete Solution

## 🎯 Problem Statement

When proxying v0.dev (and similar Next.js/Vercel applications), the following issues occurred:

1. **Blank Screen** - HTML was being returned with gzip compression, causing `ERR_CONTENT_DECODING_FAILED`
2. **404 Errors** - Static assets (`/chat-static/_next/...`, fonts, CSS) were resolving to `localhost:8000` instead of the original domain
3. **CSP Violations** - Content Security Policy headers were blocking resources from loading
4. **MIME Type Errors** - CSS files were being returned as `text/html` instead of `text/css`

## ✅ Solution Overview

The fix consists of **three critical components**:

1. **`<base>` Tag Injection** - Forces relative URLs to resolve to the original domain
2. **Content-Encoding Removal** - Prevents compression issues causing blank screens
3. **Aggressive Static Asset Bypass** - Routes static assets directly to the original domain

## 🔧 Implementation Details

### 1. Base Tag Injection (The Foundation)

**Location**: `dose/polysniffer/views.py` - Line ~1030

```python
# ─────── FINAL FIX — <base> TAG — THIS IS THE ONE THAT WINS ───────
if soup.head:
    # Remove any existing base tag
    for existing in soup.find_all('base'):
        existing.decompose()
    # Inject the ONE tag that fixes everything
    base_tag = soup.new_tag('base', href=base_url + '/')
    soup.head.insert(0, base_tag)
    print("[PROXY] <base> tag injected — v0.dev defeated")
```

**Why This Works:**
- The `<base>` tag tells the browser to resolve all relative URLs relative to the specified base URL
- Without it, relative URLs like `/chat-static/_next/...` resolve to `http://localhost:8000/chat-static/_next/...`
- With it, they resolve to `https://v0.dev/chat-static/_next/...`
- **This must be injected IMMEDIATELY after creating the soup, before any other processing**

### 2. Content-Encoding Removal (Fixes Blank Screen)

**Location**: `dose/polysniffer/views.py` - Line ~1395

```python
# ─────── FINAL FIX — NO COMPRESSION + <base> TAG ───────
# KILL COMPRESSION to prevent ERR_CONTENT_DECODING_FAILED and blank screen
# Set AFTER header copying to ensure it's never overwritten
django_response['Content-Encoding'] = ''  # ← KILL COMPRESSION

# For HTML responses, force no cache to avoid stale compressed versions
if is_html_response:
    django_response['Cache-Control'] = 'no-store, max-age=0'
```

**Why This Works:**
- Django was double-compressing or corrupting gzip-encoded responses
- Setting `Content-Encoding` to empty string prevents compression
- This must be set **AFTER** copying headers from the original response

### 3. CSP Header Removal (Fixes Blocking)

**Location**: `dose/polysniffer/views.py` - Line ~1387

```python
# Skip headers that Django handles automatically or are hop-by-hop
# CRITICAL: Also skip Content-Encoding and CSP headers to prevent compression and blocking issues
skip_headers = ['content-type', 'content-length', 'transfer-encoding', 'content-encoding',
              'content-security-policy', 'content-security-policy-report-only',
              'x-content-security-policy', 'x-frame-options']
```

**Why This Works:**
- CSP headers from the original response were blocking resources from `localhost:8000`
- By not copying CSP headers, the browser doesn't enforce restrictions
- Resources can now load from the original domain (thanks to `<base>` tag)

### 4. Aggressive Static Asset Bypass (Fixes 404s)

**Location**: `dose/polysniffer/views.py` - Line ~724

```python
# ─────── FINAL V0.DEV CHAT-STATIC FIX — THIS ONE WINS FOREVER ───────
# v0.dev uses /chat-static/_next/... for all assets
is_vercel_asset = False
if check_path_lower.startswith('chat-static/') or '/chat-static/' in check_path_lower:
    is_vercel_asset = True
    print(f"[BYPASS] Caught chat-static path: {check_path}")

# Also catch any path that contains /_next/ or ends with known extensions
if '/_next/' in check_path_lower or check_path_lower.endswith(('.woff2', '.woff', '.js', '.css', '.png', '.jpg', '.svg', '.webp')):
    is_vercel_asset = True

# For v0.dev, the real domain is always v0.dev, even if endpoint_url has /chat/...
if 'v0.dev' in endpoint.endpoint_url or 'v0.app' in endpoint.endpoint_url:
    real_domain = "https://v0.dev"
else:
    real_domain = f"{parsed_endpoint.scheme}://{parsed_endpoint.netloc}"
```

**Why This Works:**
- Static assets are detected before HTML processing
- They're fetched directly from the original domain (bypassing the proxy)
- For v0.dev, we force the domain to `https://v0.dev` regardless of the endpoint URL path
- This prevents 404s and MIME type errors

## 📋 Complete Fix Checklist

- [x] `<base>` tag injected immediately after soup creation
- [x] `Content-Encoding` set to empty string after header copying
- [x] CSP headers excluded from header copying
- [x] `chat-static/` paths detected in bypass
- [x] `/_next/` paths detected in bypass
- [x] Static file extensions detected in bypass
- [x] v0.dev domain forced to `https://v0.dev`
- [x] Cache-Control set for HTML responses

## 🧪 Testing

### Before Fix:
- ❌ Blank screen
- ❌ `ERR_CONTENT_DECODING_FAILED`
- ❌ 404s for fonts and CSS
- ❌ CSP violations blocking resources
- ❌ MIME type errors (CSS as HTML)

### After Fix:
- ✅ Full v0.dev UI loads correctly
- ✅ All fonts load from original domain
- ✅ All CSS loads from original domain
- ✅ All images load from original domain
- ✅ No CSP violations
- ✅ No 404s
- ✅ No MIME type errors

## 🎓 Key Learnings

1. **`<base>` tag is critical** - It's the foundation that makes relative URLs work correctly
2. **Compression must be disabled** - Django's compression was corrupting responses
3. **CSP headers must be removed** - They block resources when proxying
4. **Static assets must bypass proxy** - They need to load directly from the original domain
5. **Domain forcing for v0.dev** - The endpoint URL might have a path, but assets are always at root

## 🔍 Debugging Tips

If you still see issues:

1. **Check browser console** - Look for CSP violations or 404s
2. **Check network tab** - Verify assets are loading from `https://v0.dev`, not `localhost:8000`
3. **Verify `<base>` tag** - Inspect HTML source, should see `<base href="https://v0.dev/">` in `<head>`
4. **Check response headers** - `Content-Encoding` should be empty or missing
5. **Check bypass logs** - Look for `[BYPASS] Caught chat-static path:` messages

## 📝 Files Modified

- `dose/polysniffer/views.py` - Main proxy logic with all fixes

## 🚀 Deployment

1. Restart Django server
2. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
3. Test with v0.dev endpoint
4. Verify all resources load correctly

## 🙏 Credits

This solution was developed through iterative debugging with Shela's expert guidance. The key insight was that the `<base>` tag must be injected **immediately** after soup creation, and compression must be disabled to prevent blank screens.

---

**Status**: ✅ **COMPLETE** - v0.dev proxy now works perfectly with full styling and all resources loading correctly.

