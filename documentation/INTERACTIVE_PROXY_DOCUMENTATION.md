# Interactive Flask Proxy for OSTicket/Oliver Dashboard

## Overview

The `dose/interactive_proxy_flask.py` module provides a full-featured reverse proxy that allows you to preview and interact with external web applications (like OSTicket) through a local development URL. It handles complex scenarios including multi-page navigation, form submissions, AJAX requests, and asset loading while maintaining authentication sessions.

## Purpose

- **Local Preview**: Access remote applications at `http://127.0.0.1:8001/admin/osticket/`
- **URL Rewriting**: Transparently converts between external domain URLs and local proxy paths
- **Session Management**: Maintains per-client authentication and cookie sessions
- **Asset Handling**: Correctly loads CSS, JavaScript, images, and other resources
- **AJAX Interception**: Intercepts JavaScript XHR and fetch calls to rewrite URLs dynamically
- **Multi-Page Navigation**: Navigate across multiple pages while maintaining full authentication

## Architecture

### URL Mapping

The proxy operates with a simple but powerful URL mapping strategy:

- **Real Base (Remote Server)**: `https://oliverenterprises.app.saasify.cloud/scp/`
- **Proxy Base (Local)**: `http://127.0.0.1:8001/admin/osticket/`

All paths are automatically converted between these two bases.

### Request Flow

```
Browser Request
    ↓
/admin/osticket/dashboard.php
    ↓
Proxy Route Handler
    ↓
Convert to: https://oliverenterprises.app.saasify.cloud/scp/dashboard.php
    ↓
Make Request (with session cookies)
    ↓
Receive Response
    ↓
Doseify HTML (rewrite URLs back to proxy paths)
    ↓
Inject JavaScript Interceptors
    ↓
Return to Browser
    ↓
Browser renders with proxy paths
```

### Path Handling

The proxy intelligently handles different types of paths in HTML:

1. **Full URLs**:
   - Input: `https://oliverenterprises.app.saasify.cloud/scp/dashboard.php`
   - Output: `/admin/osticket/dashboard.php`

2. **Root-Relative Paths**:
   - Input: `/scp/dashboard.php`
   - Output: `/admin/osticket/dashboard.php`
   - Special handling: `/scp/` prefix is stripped to avoid duplication

3. **Relative Paths**:
   - Input: `../images/icon.png`
   - Output: `/admin/osticket/../images/icon.png`

4. **Asset Paths**:
   - Input: `/js/jquery.min.js`
   - Output: `/admin/osticket/js/jquery.min.js`

## Core Components

### 1. URL Rewriting (`doseify_html` function)

Converts outgoing HTML from the remote server:

```python
def doseify_html(html: str) -> str:
    """
    1. Replace full URLs with proxy paths
    2. Convert /scp/ paths to /admin/osticket/ paths
    3. Fix remaining root-relative paths
    4. Inject JavaScript interceptors for AJAX/fetch calls
    """
```

**String Replacements:**
- `https://oliverenterprises.app.saasify.cloud/scp/` → `/admin/osticket/`
- `https://oliverenterprises.app.saasify.cloud` → `/admin/osticket`
- `/scp/path` → `/admin/osticket/path`

**Regex Replacements:**
- `(href|src)="/scp/([^"]*)"` → `\1="/admin/osticket/\2"`
- `(href|src)="(?!/admin/osticket)(/[^"]*)"` → `\1="/admin/osticket$2"`

### 2. JavaScript Interceptors

Injected at the end of every HTML page to intercept client-side requests:

**XMLHttpRequest Interception:**
```javascript
XMLHttpRequest.prototype.open = function(method, url, ...) {
    // Converts real URLs to proxy URLs before request
    url = url.replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/');
}
```

**Fetch API Interception:**
```javascript
window.fetch = function(resource, config) {
    // Converts real URLs in fetch calls
    resource = resource.replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/');
}
```

**jQuery AJAX Interception:**
```javascript
jQuery.ajax = function(settings) {
    // Converts real URLs in jQuery AJAX calls
    settings.url = settings.url.replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/');
}
```

This enables navigation of dashboard links that use PJAX (pushState + AJAX) or any JavaScript-based navigation.

### 3. Session Management

Each client is identified by IP address and gets a dedicated `requests.Session()`:

```python
_session_store = {}  # {client_ip: requests.Session}

# Per-client session features:
- Cookie persistence across requests
- Automatic retry with exponential backoff
- Connection pooling
- SSL/TLS certificate verification
```

**Benefits:**
- Multiple users can use the proxy simultaneously without interference
- Authentication is maintained across page navigations
- Session cookies from the remote server are preserved
- Automatic recovery from temporary connection failures

### 4. Route Handler (`osticket_proxy`)

Main Flask route that processes all proxy requests:

```python
@app.route("/admin/osticket/", defaults={'path': ''})
@app.route("/admin/osticket/<path:path>", methods=["GET", "POST"])
def osticket_proxy(path):
    # 1. Strip /scp/ if present in path
    # 2. Build real target URL
    # 3. Get/create session for client
    # 4. Make request (GET or POST)
    # 5. If HTML: doseify and return
    # 6. If other: pass through unchanged
```

## Usage

### Starting the Proxy

**Option 1: Direct Flask Command**
```powershell
# From workspace root
$env:FLASK_APP='dose/interactive_proxy_flask.py'
.venv\Scripts\python -m flask run --host 127.0.0.1 --port 8001
```

**Option 2: As a Module**
```powershell
.venv\Scripts\python -m dose.interactive_proxy_flask
```

### Accessing the Proxy

**Landing Page (with quick-start button):**
```
http://127.0.0.1:8001/
```

**Direct Access (specific page):**
```
http://127.0.0.1:8001/admin/osticket/login.php
http://127.0.0.1:8001/admin/osticket/dashboard.php
http://127.0.0.1:8001/admin/osticket/kb.php
```

**Authenticated Navigation:**
Once logged in, all links and AJAX requests automatically route through the proxy.

## Configuration

To use with a different remote endpoint, edit these constants:

```python
# In dose/interactive_proxy_flask.py
REAL_BASE = "https://your-external-domain.com/api/"
PROXY_PATH = "/admin/your-app/"
```

Then restart the Flask server.

## Implementation Details

### HTML Rewriting Strategy

**Why not use urljoin()?**
- `urljoin()` treats root-relative paths as absolute, replacing the entire path
- We need to preserve the directory structure while changing the domain
- String replacement + regex is simpler and more predictable for this use case

**Why inject JavaScript interceptors?**
- OSTicket uses PJAX (pushState + AJAX) for navigation
- Regular href links are not sufficient for modern interactive apps
- JavaScript interceptors catch XHR, fetch, and jQuery AJAX calls
- This enables seamless navigation of dashboard links

### Error Handling

The proxy gracefully handles:
- **Connection errors**: Returns 502 Bad Gateway with error message
- **Timeout errors**: Connection timeout is set to 15 seconds
- **Redirect chains**: Follows redirects automatically with `allow_redirects=True`
- **Non-HTML responses**: Binary content (images, PDFs) passes through unchanged
- **Missing sessions**: Each client gets a fresh session on first request

### Performance Considerations

- **Session pooling**: Reuses HTTP connections per client
- **Retry strategy**: Exponential backoff (base 0.5s) for resilience
- **Lazy session creation**: Sessions created only on first request
- **Content-type checking**: Only rewrites HTML; passes other content directly

## Testing Verified

✅ **Functionality Tested:**
- Login page loading and form submission
- Multi-page dashboard navigation
- Asset loading (CSS, JavaScript, images)
- Form submissions
- Session persistence across requests
- AJAX/PJAX navigation (via JavaScript interceptors)
- Multiple simultaneous users
- Redirect following
- Cookie handling

## Known Limitations

1. **WebSocket Support**: Not supported; real-time features won't work
2. **JavaScript Execution Context**: Limited; some complex JS behaviors may not work as expected
3. **Binary Content**: Passed through without modification
4. **Session Timeouts**: If remote server times out, re-authentication required
5. **Complex File Uploads**: May require additional handling
6. **Server-Side Redirects**: Followed but may expose internal structure

## Future Enhancements

- [ ] WebSocket proxying for real-time features
- [ ] HTTPS endpoint support with custom certificates
- [ ] Request logging and debugging interface
- [ ] Rate limiting and security headers
- [ ] Caching layer for static assets
- [ ] Support for multiple remote endpoints
- [ ] Response compression
- [ ] Request/response inspection tools

## Files

- `dose/interactive_proxy_flask.py`: Main proxy implementation (~150 lines)
- `INTERACTIVE_PROXY_DOCUMENTATION.md`: This comprehensive documentation

## Example Workflow

1. **Start proxy:**
   ```powershell
   $env:FLASK_APP='dose/interactive_proxy_flask.py'
   .venv\Scripts\python -m flask run --host 127.0.0.1 --port 8001
   ```

2. **Open browser:**
   ```
   http://127.0.0.1:8001/
   ```

3. **Click "Load OSTicket"** or navigate to:
   ```
   http://127.0.0.1:8001/admin/osticket/login.php
   ```

4. **Log in** with remote credentials

5. **Navigate freely** - all links and AJAX requests work transparently

## Technical Notes

- **Threading**: Flask runs in single-threaded development mode; use Gunicorn for production
- **Session Storage**: In-memory dictionary; sessions lost on server restart
- **Per-Client Identification**: Based on `request.remote_addr`; doesn't work behind load balancers without X-Forwarded-For
- **CORS**: Not configured; may need adjustment for cross-origin requests

## Dependencies

- `Flask`: Web framework for routing and request handling
- `requests`: HTTP library for making remote requests
- `urllib3`: Retry logic and connection pooling

## Troubleshooting

**Issue: Links don't work**
- Check browser console for JavaScript errors
- Verify REAL_BASE and PROXY_PATH match your endpoint
- Ensure remote server is accessible from your network

**Issue: Styles/images missing**
- Check that asset paths are being rewritten (use browser inspector)
- Verify CSS and image files load with 200 status

**Issue: Form submissions fail**
- Check that POST requests reach the proxy (Flask logs)
- Verify form action attributes are being rewritten

**Issue: Session expires**
- Remote server timeout; log in again
- Consider configuring session timeout on remote server

## Next Steps (Future Development)

1. Move to `dose` package for better integration
2. Add admin UI for proxy configuration
3. Implement request logging dashboard
4. Add support for multiple remote endpoints
5. Create configuration file for persistent settings

## Migration Plan

Tomorrow's migration will move this from standalone location to the `dose` package:
- Update imports to use `from dose.interactive_proxy_flask import run`
- Create `dose/__init__.py` entry point
- Update documentation and references
- Run full regression test after migration
