# Interactive Proxy for OSTicket/Oliver Dashboard

## Overview

The `interactive_proxy_flask.py` module provides a reverse proxy that allows you to preview and interact with external endpoints (like OSTicket) through a local development URL (`http://127.0.0.1:8001/admin/osticket/`).

## Purpose

- **URL Rewriting**: Converts external domain URLs to local proxy paths and vice versa
- **Session Management**: Maintains per-client cookie sessions for authenticated access
- **Asset Loading**: Properly handles CSS, JS, and image asset paths
- **Multi-Page Navigation**: Supports navigation across multiple pages while maintaining authentication

## Architecture

### URL Mapping

- **Real Base**: `https://oliverenterprises.app.saasify.cloud/scp/`
- **Proxy Base**: `http://127.0.0.1:8001/admin/osticket/`

The proxy automatically converts between these paths:
- Incoming requests: `/admin/osticket/path` → `https://oliverenterprises.app.saasify.cloud/scp/path`
- Response HTML: Real URLs are replaced with proxy paths for browser rendering

### Path Handling

The proxy intelligently handles different path types in HTML:

1. **Full URLs**: `https://oliverenterprises.app.saasify.cloud/...` → `/admin/osticket/...`
2. **Root-Relative Paths**: `/scp/page.php` → `/admin/osticket/page.php`
3. **Relative Paths**: `../images/icon.png` → `/admin/osticket/../images/icon.png`

Duplicate `/scp/` paths are automatically stripped to prevent 404 errors.

## Usage

### Starting the Proxy

```powershell
# Set environment variables
$env:FLASK_APP='dose/interactive_proxy_flask.py'

# Run Flask development server
.venv\Scripts\python -m flask run --host 127.0.0.1 --port 8001
```

### Accessing the Proxy

1. **Landing Page**: `http://127.0.0.1:8001/`
   - Simple button to load OSTicket login page

2. **Direct Access**: `http://127.0.0.1:8001/admin/osticket/login.php`
   - Access specific pages directly

3. **After Authentication**: Navigate freely through authenticated pages

## Implementation Details

### Key Functions

#### `doseify_html(html: str) -> str`
Converts outgoing HTML from the remote server:
- Replaces `https://oliverenterprises.app.saasify.cloud/scp/` with `/admin/osticket/`
- Converts root-relative paths like `/scp/dashboard.php` to `/admin/osticket/dashboard.php`
- Strips duplicate `/scp/` prefixes in paths
- Uses regex to safely rewrite href and src attributes

#### `osticket_proxy(path)` Route Handler
Main proxy route that:
- Receives requests at `/admin/osticket/<path>`
- Builds target URL from `REAL_BASE` + path
- Manages per-client session storage for cookie persistence
- Makes HTTP requests with retries
- Doseifies HTML responses before returning to browser
- Passes through non-HTML content unchanged

### Session Management

Each client (identified by IP address) gets its own `requests.Session()` object:
- **Cookie Persistence**: Cookies set by the remote server are maintained across requests
- **Retry Logic**: Automatic retries with exponential backoff for resilient connections
- **Per-Client Isolation**: Multiple users can access the proxy simultaneously without session interference

## Configuration

Edit these constants in `interactive_proxy_flask.py` to use different endpoints:

```python
REAL_BASE = "https://oliverenterprises.app.saasify.cloud/scp/"
PROXY_PATH = "/admin/osticket/"
```

## Limitations

- **JavaScript-Heavy Interactions**: Only basic link navigation works; complex JavaScript interactions may not function
- **Form POST Handling**: Simple form submissions work; complex multi-step forms may need additional handling
- **Session Timeouts**: If the remote server times out your session, you'll need to re-authenticate
- **Non-HTML Content**: Binary files (PDFs, images) are passed through unchanged without path rewriting

## Testing

The proxy has been tested with:
- ✅ Login page loading and authentication
- ✅ Multi-page dashboard navigation
- ✅ Asset loading (CSS, JS, images)
- ✅ Form submissions
- ✅ Session persistence across requests
- ⚠️ Complex interactive elements (limited support)

## Files

- `dose/interactive_proxy_flask.py`: Main proxy implementation
- `dose/INTERACTIVE_PROXY_README.md`: This documentation

## Future Enhancements

- Support for JavaScript-based redirects
- WebSocket proxying for real-time features
- AJAX request interception
- Query parameter preservation in path rewriting
- TLS/SSL certificate handling for HTTPS endpoints
