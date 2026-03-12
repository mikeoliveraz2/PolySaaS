# dose/polysniffer/views/proxy.py - 2026-01-17 22:35 PST

from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from urllib.parse import urlparse, urlencode
from bs4 import BeautifulSoup
import requests
import json
from .core import get_endpoint_any_schema, is_static_asset, rewrite_static_url, convert_relative_static_to_absolute

@csrf_exempt
@xframe_options_exempt
@staff_member_required
def scp_catchall(request, path=''):
    return HttpResponse("Not found", status=404)

@csrf_exempt
@xframe_options_exempt
@staff_member_required
def proxy_capture(request, endpoint_id, path=''):
    """
    Main proxy function - captures and proxies requests to external endpoints
    """
    if not request.user.is_staff:
        return HttpResponseForbidden('Staff access required')

    try:
        endpoint = get_endpoint_any_schema(endpoint_id, request)
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html><head><title>PolySniffer Error</title></head>
        <body style="font-family: system-ui; padding: 40px; background: #1a1a1a; color: #f00;">
            <h1>Error Loading Endpoint</h1>
            <p>Could not find endpoint with ID: {endpoint_id}</p>
            <p>Error: {str(e)}</p>
            <p><a href="/admin/dose/passthroughendpoint/" style="color: #0f0;">Back to Endpoints</a></p>
        </body></html>
        """
        return HttpResponse(error_html, status=404)

    # Build target URL
    target_url = endpoint.endpoint_url
    if path:
        if not target_url.endswith('/'):
            target_url += '/'
        target_url += path.lstrip('/')

    # Add query parameters
    if request.GET:
        query_string = urlencode(request.GET)
        separator = '&' if '?' in target_url else '?'
        target_url += separator + query_string

    # Parse endpoint URL for base_url
    parsed_endpoint = urlparse(endpoint.endpoint_url)
    base_url = f"{parsed_endpoint.scheme}://{parsed_endpoint.netloc}"

    # Create session for requests
    session = requests.Session()

    # Forward cookies from Django session (for auth persistence)
    if hasattr(request, 'session'):
        # Forward v0.dev cookies if available
        if 'v0_dev_cookies' in request.session:
            for name, value in request.session['v0_dev_cookies'].items():
                session.cookies.set(name, value, domain=parsed_endpoint.netloc)

    # Forward current request cookies
    for name, value in request.COOKIES.items():
        session.cookies.set(name, value, domain=parsed_endpoint.netloc)

    # Prepare request
    method = request.method
    headers = {}

    # Copy headers (exclude Django-specific ones)
    exclude_headers = {'CONTENT_LENGTH', 'CONTENT_TYPE', 'HTTP_HOST', 'HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP'}
    for header_name, header_value in request.META.items():
        if header_name.startswith('HTTP_') and header_name not in exclude_headers:
            django_header = header_name[5:].replace('_', '-').title()
            headers[django_header] = header_value
        elif header_name == 'CONTENT_TYPE':
            headers['Content-Type'] = header_value

    # Handle request body
    data = None
    if method in ['POST', 'PUT', 'PATCH']:
        if request.content_type and 'multipart' in request.content_type:
            # Handle file uploads
            data = request.POST.copy()
            files = {}
            for field_name, file_obj in request.FILES.items():
                files[field_name] = (file_obj.name, file_obj.read(), file_obj.content_type)
            # For multipart, we need to use files parameter
            response = session.request(method, target_url, headers=headers, data=data, files=files)
        else:
            data = request.body
            response = session.request(method, target_url, headers=headers, data=data)
    else:
        response = session.request(method, target_url, headers=headers)

    content_type = response.headers.get('content-type', '').lower()
    is_html_response = 'text/html' in content_type

    # Get handler if available
    handler = None
    handler_class = getattr(endpoint, "handler_class", None)
    if handler_class:
        try:
            handler_module, handler_class = handler_class.rsplit('.', 1)
            handler = getattr(__import__(handler_module, fromlist=[handler_class]), handler_class)(endpoint)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load handler {handler_class}: {e}")

    response_text = None
    if is_html_response:
        try:
            response_text = response.content.decode('utf-8', errors='ignore')
        except:
            response_text = str(response.content)

    # HTML processing
    if is_html_response:
        # Check for Vercel auth redirect
        if '"Missing shareableToken"' in response_text:
            from django.http import HttpResponseRedirect
            from urllib.parse import quote
            proxy_return = f"https://polysaas.online/admin/polysniffer/proxy/{endpoint_id}/"
            vercel_auth_url = f"https://vercel.com/login/v0?next={quote(proxy_return)}"
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[V0 AUTH] Detected Missing shareableToken — REDIRECTING to Vercel Auth: {vercel_auth_url}")
            return HttpResponseRedirect(vercel_auth_url)

        proxy_base = f'/admin/polysniffer/proxy/{endpoint_id}/'

        # Try handler first
        if handler:
            try:
                handler_result = handler.process_html_response(
                    response_text,
                    response,
                    target_url,
                    base_url,
                    request=request
                )
                if handler_result and handler_result[0] is not None:
                    processed_html, django_response = handler_result
                    # Inject capture script for handler-processed HTML
                    if processed_html and isinstance(processed_html, str):
                        capture_script = f"""
<script>
(function() {{
    if (window.POLYSNIFFER_CAPTURE) return;
    window.POLYSNIFFER_CAPTURE = true;

    const isInIframe = window.self !== window.top;

    function sendCapture(payload) {{
        if (isInIframe) {{
            window.parent.postMessage({{
                type: 'polysniffer-capture',
                payload: payload
            }}, '*');
        }}
    }}

    // Intercept fetch
    if (window.fetch) {{
        const originalFetch = window.fetch;
        window.fetch = function(...args) {{
            const url = typeof args[0] === 'string' ? args[0] : args[0].url;
            const method = args[1]?.method || 'GET';

            const promise = originalFetch.apply(this, args);

            promise.then(response => {{
                sendCapture({{
                    method: method,
                    url: url,
                    status: response.status,
                    statusText: response.statusText,
                    timestamp: new Date().toISOString()
                }});
                return response;
            }}).catch(error => {{
                sendCapture({{
                    method: method,
                    url: url,
                    status: 0,
                    statusText: 'Error',
                    error: error.message,
                    timestamp: new Date().toISOString()
                }});
                throw error;
            }});

            return promise;
        }};
    }}

    // Intercept XMLHttpRequest
    if (window.XMLHttpRequest) {{
        const originalOpen = XMLHttpRequest.prototype.open;
        const originalSend = XMLHttpRequest.prototype.send;

        XMLHttpRequest.prototype.open = function(method, url, ...rest) {{
            this._polysniffer_method = method;
            this._polysniffer_url = url;
            return originalOpen.apply(this, [method, url, ...rest]);
        }};

        XMLHttpRequest.prototype.send = function(...args) {{
            const xhr = this;
            const method = xhr._polysniffer_method || 'GET';
            const url = xhr._polysniffer_url || '';

            xhr.addEventListener('loadend', function() {{
                sendCapture({{
                    method: method,
                    url: url,
                    status: xhr.status,
                    statusText: xhr.statusText,
                    timestamp: new Date().toISOString()
                }});
            }});

            return originalSend.apply(this, args);
        }};
    }}

    console.log("%c🟢 PolySniffer CAPTURE ACTIVE" + (isInIframe ? " (iframe mode)" : ""), "color:#0f0;font-size:16px");
}})();
</script>
"""
                        soup = BeautifulSoup(processed_html, 'html.parser')
                        if soup.head:
                            soup.head.append(capture_script)
                        processed_html = str(soup)
                        django_response.content = processed_html.encode('utf-8')
                        return django_response
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"[POLYSNIFFER] Handler HTML processing failed for endpoint {endpoint_id}: {e}")

        # Fallback HTML processing
        try:
            soup = BeautifulSoup(response_text, 'html.parser')

            # Inject base tag
            if soup.head:
                for existing in soup.find_all('base'):
                    existing.decompose()
                base_tag = soup.new_tag('base', href=base_url + '/')
                soup.head.insert(0, base_tag)

            # Inject capture script
            if soup.head:
                capture_script = soup.new_tag('script')
                capture_script.string = f"""
(function() {{
    'use strict';
    const CAPTURE_URL = window.location.origin + '/admin/polysniffer/silent-capture/{endpoint_id}/';
    const PROXY_BASE = '{proxy_base}';
    const BASE_URL = '{base_url}';
    const isInIframe = window.self !== window.top;

    // Send capture data to parent window (for iframe mode) or to capture endpoint
    function sendCapture(type, data, url) {{
        const payload = {{
            type: type,
            url: url || window.location.href,
            data: data,
            timestamp: new Date().toISOString()
        }};
        
        // Send to parent window if in iframe
        if (isInIframe) {{
            window.parent.postMessage({{
                type: 'polysniffer-capture',
                payload: payload
            }}, '*');
        }}
        
        // Also send to silent capture endpoint
        try {{
            navigator.sendBeacon(CAPTURE_URL, JSON.stringify(payload));
        }} catch (e) {{
            console.log('[PolySniffer] Capture beacon failed:', e);
        }}
    }}

    function shouldProxy(url) {{
        if (!url) return false;
        const urlLower = url.toLowerCase();
        const staticPaths = ['/_next/', '/chat-static/', '/static/', '/assets/', '/css/', '/js/', '/fonts/', '/images/', '/image'];
        const staticExts = ['.css', '.js', '.woff', '.woff2', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.json', '.webp'];
        if (staticPaths.some(p => url.includes(p))) return false;
        if (staticExts.some(ext => urlLower.endsWith(ext))) return false;
        return true;
    }}

    function rewriteToProxy(url) {{
        if (!url || !shouldProxy(url)) return url;
        if (url.startsWith(PROXY_BASE) || url.startsWith('/admin/polysniffer/proxy/')) return url;
        if (url.startsWith('#') || url.startsWith('javascript:') || url.startsWith('data:') || url.startsWith('mailto:')) return url;

        try {{
            if (url.startsWith('http://') || url.startsWith('https://')) {{
                const urlObj = new URL(url);
                if (urlObj.origin === BASE_URL) {{
                    const path = urlObj.pathname + urlObj.search + urlObj.hash;
                    return PROXY_BASE + path.replace(/^\\//, '');
                }}
            }}
            if (url.startsWith('/')) {{
                return PROXY_BASE + url.replace(/^\\//, '');
            }}
            const currentPath = window.location.pathname;
            const proxyPath = currentPath.replace(/^\\/admin\\/polysniffer\\/proxy\\/\\d+\\//, '');
            const basePath = proxyPath.substring(0, proxyPath.lastIndexOf('/') + 1);
            return PROXY_BASE + basePath + url;
        }} catch (e) {{
            return url;
        }}
    }}

    // Intercept form submissions
    document.addEventListener('submit', function(e) {{
        const form = e.target;
        if (form.tagName === 'FORM') {{
            const action = form.getAttribute('action') || form.action || '';
            if (action && shouldProxy(action) && !action.startsWith(PROXY_BASE) && !action.startsWith('/admin/polysniffer/proxy/')) {{
                const newAction = rewriteToProxy(action);
                form.setAttribute('action', newAction);
                form.action = newAction;
            }}
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            sendCapture('form_submit', {{
                action: form.action || window.location.href,
                method: form.method || 'GET',
                data: data
            }}, form.action || window.location.href);
        }}
    }}, true);

    // Intercept clicks
    document.addEventListener('click', function(e) {{
        const clickable = e.target.closest('button, input[type="submit"], input[type="button"], [role="button"], a, [onclick]');
        if (clickable) {{
            const form = clickable.closest('form');
            if (form && form.tagName === 'FORM') {{
                const action = form.getAttribute('action') || form.action || '';
                if (action && shouldProxy(action) && !action.startsWith(PROXY_BASE) && !action.startsWith('/admin/polysniffer/proxy/')) {{
                    const newAction = rewriteToProxy(action);
                    form.setAttribute('action', newAction);
                    form.action = newAction;
                }}
            }}
            const onclick = clickable.getAttribute('onclick');
            const href = clickable.getAttribute('href') || clickable.href;
            const dataHref = clickable.getAttribute('data-href');
            const dataUrl = clickable.getAttribute('data-url');
            const dataAction = clickable.getAttribute('data-action');
            const navUrl = href || dataHref || dataUrl || dataAction;
            if (navUrl && shouldProxy(navUrl) && !navUrl.startsWith(PROXY_BASE) && !navUrl.startsWith('/admin/polysniffer/proxy/')) {{
                const newUrl = rewriteToProxy(navUrl);
                if (href) {{
                    clickable.setAttribute('href', newUrl);
                    clickable.href = newUrl;
                }} else if (dataHref) {{
                    clickable.setAttribute('data-href', newUrl);
                }} else if (dataUrl) {{
                    clickable.setAttribute('data-url', newUrl);
                }} else if (dataAction) {{
                    clickable.setAttribute('data-action', newUrl);
                }}
            }}
        }}
    }}, true);

    // Intercept programmatic form submissions
    const originalSubmit = HTMLFormElement.prototype.submit;
    HTMLFormElement.prototype.submit = function() {{
        const action = this.getAttribute('action') || this.action || '';
        if (action && shouldProxy(action) && !action.startsWith(PROXY_BASE) && !action.startsWith('/admin/polysniffer/proxy/')) {{
            const newAction = rewriteToProxy(action);
            this.setAttribute('action', newAction);
            this.action = newAction;
        }}
        return originalSubmit.call(this);
    }};

    // Intercept fetch
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {{
        const [url, options = {{}}] = args;
        if (typeof url === 'string') {{
            const rewritten = rewriteStaticAssetUrl(url);
            if (rewritten !== url) {{
                args[0] = rewritten;
            }}
        }}
        if (options && (options.method === 'POST' || options.method === 'PUT' || options.method === 'PATCH')) {{
            if (shouldProxy(args[0]) && !args[0].startsWith(PROXY_BASE) && !args[0].startsWith('/admin/polysniffer/proxy/')) {{
                const newUrl = rewriteToProxy(args[0]);
                args[0] = newUrl;
            }}
            sendCapture('fetch', {{
                method: options.method || 'GET',
                url: args[0],
                headers: Object.fromEntries(new Headers(options.headers || {{}})),
                body: options.body ? (typeof options.body === 'string' ? options.body : JSON.stringify(options.body)) : null
            }}, args[0]);
        }}
        return originalFetch.apply(this, args);
    }};

    // Intercept XHR
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url) {{
        this._method = method;
        if ((method === 'POST' || method === 'PUT' || method === 'PATCH') && shouldProxy(url) && !url.startsWith(PROXY_BASE) && !url.startsWith('/admin/polysniffer/proxy/')) {{
            const newUrl = rewriteToProxy(url);
            this._url = newUrl;
            return originalXHROpen.call(this, method, newUrl);
        }}
        this._url = url;
        return originalXHROpen.apply(this, arguments);
    }};

    XMLHttpRequest.prototype.send = function(body) {{
        if (this._method === 'POST' || this._method === 'PUT' || this._method === 'PATCH') {{
            sendCapture('xhr', {{
                method: this._method,
                url: this._url,
                body: body ? (typeof body === 'string' ? body : JSON.stringify(body)) : null
            }}, this._url);
        }}
        return originalXHRSend.apply(this, arguments);
    }};

    // Capture navigation
    let lastUrl = window.location.href;
    setInterval(function() {{
        if (window.location.href !== lastUrl) {{
            lastUrl = window.location.href;
            sendCapture('navigation', {{
                url: lastUrl
            }}, lastUrl);
        }}
    }}, 1000);

    // Capture page load
    sendCapture('page_load', {{
        url: window.location.href,
        cookies: document.cookie
    }}, window.location.href);

    // Capture on unload
    window.addEventListener('beforeunload', function() {{
        sendCapture('page_unload', {{
            url: window.location.href,
            cookies: document.cookie
        }}, window.location.href);
    }});

    // Helper: Check if URL is a static asset
    function isStaticAsset(url) {{
        if (!url) return false;
        const urlLower = url.toLowerCase();
        const staticPaths = ['/_next/', '/chat-static/', '/static/', '/assets/', '/css/', '/js/', '/fonts/', '/images/', '/image', 'image?', 'draft-preview', 'manifest.json'];
        const staticExts = ['.css', '.js', '.woff', '.woff2', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.json', '.webp', '.ttf', '.otf', '.eot'];
        if (staticPaths.some(p => url.includes(p))) return true;
        if (staticExts.some(ext => urlLower.endsWith(ext))) return true;
        if (urlLower.includes('image?') || urlLower.includes('/_next/image')) return true;
        if (urlLower.includes('draft-preview')) return true;
        if (urlLower.includes('manifest.json')) return true;
        return false;
    }}

    // Helper: Rewrite static asset URL to original domain
    function rewriteStaticAssetUrl(url) {{
        if (!url) return url;
        if (url.includes('localhost') || url.includes('127.0.0.1') || url.includes(':8000')) {{
            if (url.includes('/chat-static/') || url.includes('/_next/') || isStaticAsset(url)) {{
                try {{
                    const urlObj = new URL(url);
                    return BASE_URL + urlObj.pathname + urlObj.search;
                }} catch (e) {{
                    const match = url.match(/https?:\\/\\/[^/]+(\\/[^\\s"\'<>)]*)/);
                    if (match) {{
                        return BASE_URL + match[1];
                    }}
                    return url;
                }}
            }}
        }}
        const isStatic = isStaticAsset(url);
        if (url.startsWith('http://') || url.startsWith('https://')) {{
            return url;
        }}
        if (url.startsWith('/')) {{
            if (isStatic) {{
                return BASE_URL + url;
            }}
            return PROXY_BASE + url.substring(1);
        }}
        if (isStatic) {{
            return BASE_URL + '/' + url;
        }}
        return PROXY_BASE + url;
    }}

    // Intercept link clicks
    document.addEventListener('click', function(e) {{
        const link = e.target.closest('a');
        if (link && link.href) {{
            const hrefAttr = link.getAttribute('href');
            const hrefResolved = link.href;
            if (hrefAttr && !hrefAttr.startsWith('#') && !hrefAttr.startsWith('javascript:') && !hrefAttr.startsWith('data:') &&
                !hrefAttr.startsWith(PROXY_BASE) && !hrefAttr.startsWith('/admin/polysniffer/proxy/') && !isStaticAsset(hrefAttr)) {{
                const newHref = rewriteNavigationUrl(hrefAttr);
                if (newHref !== hrefAttr && newHref !== hrefResolved) {{
                    e.preventDefault();
                    e.stopPropagation();
                    window.location.href = newHref;
                    return false;
                }}
            }}
            if (hrefResolved && !hrefResolved.startsWith(window.location.origin + PROXY_BASE) &&
                     !hrefResolved.startsWith(window.location.origin + '/admin/polysniffer/proxy/') &&
                     (hrefResolved.startsWith(BASE_URL) || hrefResolved.startsWith(window.location.origin)) &&
                     !isStaticAsset(hrefResolved)) {{
                try {{
                    const urlObj = new URL(hrefResolved);
                    const path = urlObj.pathname + urlObj.search + urlObj.hash;
                    const newHref = window.location.origin + PROXY_BASE + path.replace(/^\\//, '');
                    e.preventDefault();
                    e.stopPropagation();
                    window.location.href = newHref;
                    return false;
                }} catch (e) {{
                }}
            }}
        }}
    }}, true);

    // Helper: Rewrite navigation URL to go through proxy
    function rewriteNavigationUrl(url) {{
        if (!url) return url;
        if (url.startsWith(PROXY_BASE) || url.startsWith('/admin/polysniffer/proxy/')) return url;
        if (url.startsWith('#') || url.startsWith('javascript:') || url.startsWith('data:') || url.startsWith('mailto:')) return url;
        if (isStaticAsset(url)) return url;

        try {{
            if (url.startsWith('http://') || url.startsWith('https://')) {{
                const urlObj = new URL(url);
                if (urlObj.origin === BASE_URL) {{
                    const path = urlObj.pathname + urlObj.search + urlObj.hash;
                    return PROXY_BASE + path.replace(/^\\//, '');
                }}
                return url;
            }}
            if (url.startsWith('/')) {{
                return PROXY_BASE + url.substring(1);
            }}
            const currentPath = window.location.pathname;
            const proxyPath = currentPath.replace(/^\\/admin\\/polysniffer\\/proxy\\/\\d+\\//, '');
            const basePath = proxyPath.substring(0, proxyPath.lastIndexOf('/') + 1);
            return PROXY_BASE + basePath + url;
        }} catch (e) {{
            return url;
        }}
    }}

    // Rewrite existing DOM elements
    function rewriteExistingElements() {{
        document.querySelectorAll('link[href]').forEach(function(link) {{
            const href = link.getAttribute('href');
            if (href && (href.includes('localhost') || href.includes('127.0.0.1') || href.includes(':8000'))) {{
                const newHref = rewriteStaticAssetUrl(href);
                if (newHref !== href) {{
                    link.setAttribute('href', newHref);
                    link.href = newHref;
                }}
            }}
        }});

        document.querySelectorAll('script[src]').forEach(function(script) {{
            const src = script.getAttribute('src');
            if (src && (src.includes('localhost') || src.includes('127.0.0.1') || src.includes(':8000'))) {{
                const newSrc = rewriteStaticAssetUrl(src);
                if (newSrc !== src) {{
                    script.setAttribute('src', newSrc);
                    script.src = newSrc;
                }}
            }}
        }});

        document.querySelectorAll('img[src]').forEach(function(img) {{
            const src = img.getAttribute('src');
            if (src && (src.includes('localhost') || src.includes('127.0.0.1') || src.includes(':8000'))) {{
                const newSrc = rewriteStaticAssetUrl(src);
                if (newSrc !== src) {{
                    img.setAttribute('src', newSrc);
                    img.src = newSrc;
                }}
            }}
        }});
    }}

    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', rewriteExistingElements);
    }} else {{
        rewriteExistingElements();
    }}
    setTimeout(rewriteExistingElements, 100);
    setTimeout(rewriteExistingElements, 500);
}})();
"""
                soup.head.append(capture_script)

            # Inject green bar
            if soup.body:
                green_bar_script = """
<script>
(function() {
    if (window.POLYSNIFFER_GREEN) return;
    window.POLYSNIFFER_GREEN = true;

    let count = 0;

    function createBar() {
        const old = document.getElementById('polysniffer-green');
        if (old) old.remove();

        const bar = document.createElement('div');
        bar.id = 'polysniffer-green';
        bar.style.cssText = `
            position: fixed !important;
            top: 0 !important; left: 0 !important; right: 0 !important;
            height: 44px !important;
            background: #000 !important;
            color: #0f0 !important;
            font: bold 14px 'Courier New', monospace !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            z-index: 2147483647 !important;
            border-bottom: 3px solid #0f0 !important;
            box-shadow: 0 4px 20px rgba(0,255,0,0.6) !important;
            pointer-events: none !important;
        `;
        bar.innerHTML = `🟢 PolySniffer ACTIVE — Capturing all traffic — <span id="ps-count">0</span> requests`;
        document.documentElement.appendChild(bar);
    }

    createBar();

    setInterval(() => {
        count++;
        const c = document.getElementById('ps-count');
        if (c) c.textContent = count;
    }, 1000);

    new MutationObserver(createBar).observe(document.documentElement, {
        childList: true,
        subtree: true
    });

    console.log("%c🟢 PolySniffer UNKILLABLE GREEN BAR ACTIVE", "color:#0f0;font-size:20px");
})();
</script>
"""
                soup.body.insert(0, BeautifulSoup(green_bar_script, 'html.parser'))

            response_text = str(soup)
            response_content = response_text.encode('utf-8')

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"HTML processing failed: {e}")
            response_content = response.content

    else:
        response_content = response.content

    django_response = HttpResponse(
        response_content,
        status=response.status_code,
        content_type=content_type
    )

    # Forward cookies
    for cookie in session.cookies:
        try:
            django_response.set_cookie(
                cookie.name,
                cookie.value,
                domain=None,
                path=cookie.path if cookie.path else '/',
                secure=cookie.secure if cookie.secure else False,
                httponly=True
            )
        except Exception as e:
            pass

    # Copy headers
    hop_by_hop_headers = {
        'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
        'te', 'trailers', 'transfer-encoding', 'upgrade'
    }

    for header_name, header_value in response.headers.items():
        header_lower = header_name.lower()
        skip_headers = ['content-type', 'content-length', 'transfer-encoding', 'content-encoding',
                      'content-security-policy', 'content-security-policy-report-only',
                      'x-content-security-policy', 'x-frame-options', 'frame-options']
        if header_lower not in skip_headers and header_lower not in hop_by_hop_headers:
            if header_lower == 'set-cookie':
                cookie_value = header_value
                cookie_parts = cookie_value.split(';')
                filtered_parts = [part for part in cookie_parts if not part.strip().lower().startswith('domain=')]
                cookie_value = '; '.join(filtered_parts)
                django_response[header_name] = cookie_value
            else:
                django_response[header_name] = header_value

    django_response['Content-Encoding'] = ''

    if is_html_response:
        django_response['Cache-Control'] = 'no-store, max-age=0'

    return django_response