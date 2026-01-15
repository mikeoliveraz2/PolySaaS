# Iframe-Hostile App Passthrough Pattern

## Overview
This document outlines the official pattern for integrating iframe-hostile applications (like Nextcloud, Zammad, OSTicket) into the DoseV3MasterSaaS passthrough system.

## Problem
Iframe-hostile apps implement strict Content Security Policies (CSP) and X-Frame-Options that prevent them from being embedded in iframes. This causes:
- White screens on initial load
- CSP violations blocking assets
- Broken user experience

## Solution: Native Login + Live Proxy Pattern

### Architecture
1. **Native Login Page**: Serve a static/native login page for initial entry points (e.g., "/login")
2. **Live Proxy**: Use real application HTML with URL rewriting for all other pages
3. **Seamless Transition**: After login, user gets full live application experience

### Implementation Template

```python
def proxy_request(self, target_url):
    # ... existing session setup ...

    response = session.get(target_url, headers=headers, timeout=30, allow_redirects=False)
    response.headers.pop("X-Frame-Options", None)

    # --------------------------------------------------------------
    # IF/THEN/ELSE TREE FOR IFRAME-HOSTILE APPS
    # --------------------------------------------------------------
    if response.status_code == 200 and 'text/html' in response.headers.get('content-type', ''):
        html = response.text

        # 1. IF entry point (login, index, etc.) → serve native page
        if self.is_entry_point_request():
            logger.info(f"[{self.app_name}] Entry point detected – serving native page")
            html = self.get_native_page_html()

        # 2. ELSE – use real app HTML with URL rewriting
        else:
            logger.info(f"[{self.app_name}] Using real app HTML with proxy rewriting")
            proxy_base = f"/{self.endpoint.trigger_path}".rstrip('/')
            base_url = self.get_base_url(self.endpoint.endpoint_url)
            processed = self.process_html_response(html, response, target_url, proxy_base, base_url)
            if processed:
                html = processed

        # Wrap in admin template
        from django.template.loader import render_to_string
        wrapped_html = render_to_string('admin/passthrough_template.html', {
            'processed_html': mark_safe(html),
            'title': self.app_name
        }, request=self.request)

        return HttpResponse(wrapped_html, content_type='text/html')

    # Non-HTML responses (CSS, JS, images, etc.)
    return HttpResponse(response.content, content_type=response.headers.get('content-type'))
```

### Key Components

#### 1. Entry Point Detection
```python
def is_entry_point_request(self):
    """Detect if this is an entry point that needs native page"""
    entry_paths = ['/login', '/index', '/']
    return any(path in self.request.path.lower() for path in entry_paths)
```

#### 2. Native Page Template
- Create `templates/passthrough/{app}_login.html`
- Static HTML that mimics the app's login page
- All asset URLs rewritten to proxy paths
- Form action points to proxy endpoint

#### 3. URL Rewriting
- Use BeautifulSoup to parse and rewrite all URLs
- Relative URLs: `/css/app.css` → `/pt/admin/{app}/css/app.css`
- Absolute URLs: `https://app.com/css/app.css` → `/pt/admin/{app}/css/app.css`

## Nextcloud Implementation

### Files Modified
- `dose/passthrough_handlers/nextcloud_handler.py`
- `templates/passthrough/nextcloud_login.html`

### Pattern Applied
- `/login` requests → native login page
- All other requests → live Nextcloud with URL rewriting

### Results
- ✅ Instant loading (no white screen)
- ✅ Full Nextcloud functionality after login
- ✅ All assets properly proxied
- ✅ CSP compliant

## Usage for New Apps

1. **Create Handler**: Extend `PassthroughHandler`
2. **Add Entry Point Detection**: Implement `is_entry_point_request()`
3. **Create Native Template**: `templates/passthrough/{app}_login.html`
4. **Implement URL Rewriting**: Use `map_urls_in_html()` method
5. **Apply If/Then/Else Tree**: Copy the response handling logic

## Benefits
- **Immediate Loading**: No white screen delays
- **Full Functionality**: Live app experience after entry
- **CSP Compliant**: No iframe violations
- **Maintainable**: Clear separation of concerns
- **Reusable**: Same pattern for any iframe-hostile app

## Next: Zammad
Apply this exact pattern to Zammad integration.

## Status
✅ **Official Pattern** - Use this for all iframe-hostile applications</content>
<parameter name="filePath">c:\Users\PC\OneDrive\Documents\GitHub\DoseV3MasterSaaS-main-main\documentation\IFRAME_HOSTILE_APP_PATTERN.md