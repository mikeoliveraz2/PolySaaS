"""
AI Analysis Engine for PolySniffer Captures
Analyzes captured traffic and generates handler code automatically
"""
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
def analyze_polysniffer_capture(endpoint_host, capture_session_id):
    """
    Analyze one completed Native capture session and generate draft handler code.

    Returns structured analysis that AI can use to generate handlers.
    """
    from dose.models import PassThroughEndpoint
    from .models import TrafficCapture, TrafficLog

    endpoint_matches = [
        endpoint
        for endpoint in PassThroughEndpoint.objects.all()
        if urlparse((endpoint.endpoint_url or "").strip()).netloc == endpoint_host
    ]
    if len(endpoint_matches) != 1:
        raise ValueError("Endpoint host must identify exactly one tenant endpoint")
    endpoint = endpoint_matches[0]

    capture_session = TrafficCapture.objects.filter(
        id=capture_session_id,
        is_active=False,
        capture_name__startswith=f"{endpoint_host}-native-",
    ).first()
    if capture_session is None:
        raise ValueError("Select a completed Native capture session for this endpoint")

    captures = TrafficLog.objects.filter(
        capture_session=capture_session,
        capture_source=TrafficLog.CAPTURE_NATIVE,
    ).order_by('captured_at')

    if not captures.exists():
        return {
            "error": "No Native traffic found in the selected capture session",
            "capture_session_id": capture_session_id,
            "tenant_schema": capture_session.tenant.schema_name,
        }

    analysis = {
        "endpoint_host": endpoint_host,
        "endpoint_url": endpoint.endpoint_url,
        "capture_session_id": capture_session_id,
        "tenant_schema": capture_session.tenant.schema_name,
        "base_url": extract_base_url(endpoint.endpoint_url),
        "authentication": analyze_authentication_flow(captures),
        "request_patterns": analyze_request_patterns(captures),
        "response_patterns": analyze_response_patterns(captures),
        "form_analysis": analyze_forms(captures),
        "cookie_analysis": analyze_cookies(captures),
        "ajax_endpoints": analyze_ajax_calls(captures),
        "handler_code": None  # Will be generated
    }

    # Generate handler code from analysis
    if analysis["authentication"]["method"]:
        analysis["handler_code"] = generate_handler_code(analysis, endpoint)

    return analysis


def extract_base_url(url):
    """Extract base URL from endpoint URL"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def analyze_authentication_flow(captures):
    """Analyze authentication flow from captures"""
    auth_analysis = {
        "method": None,
        "login_url": None,
        "csrf_token_field": None,
        "csrf_token_source": None,
        "username_field": None,
        "password_field": None,
        "submit_method": None,
        "submit_url": None,
        "submit_headers": {},
        "required_cookies": [],
        "session_cookie": None
    }

    captures_list = list(captures)

    login_captures = [c for c in captures_list if 'login' in (c.url or '').lower() or 'login' in (c.path or '').lower()]
    if not login_captures:
        return auth_analysis

    login_capture = login_captures[0]
    auth_analysis["login_url"] = login_capture.url

    response_body = login_capture.response_body or ''
    if response_body:
        try:
            soup = BeautifulSoup(response_body, 'html.parser')
        except Exception:
            soup = None

        if soup:
            form = soup.find('form')
            if form:
                auth_analysis["method"] = "form_based"
                auth_analysis["submit_url"] = form.get('action') or login_capture.url
                auth_analysis["submit_method"] = form.get('method', 'POST').upper()

                csrf_input = soup.find('input', {'name': re.compile(r'csrf|token', re.I)})
                if csrf_input:
                    auth_analysis["csrf_token_field"] = csrf_input.get('name')
                    auth_analysis["csrf_token_source"] = f"input[name='{csrf_input.get('name')}']"

                username_input = soup.find('input', {'type': 'text'}) or soup.find('input', {'name': re.compile(r'user|email|login', re.I)})
                password_input = soup.find('input', {'type': 'password'})

                if username_input:
                    auth_analysis["username_field"] = username_input.get('name') or 'username'
                if password_input:
                    auth_analysis["password_field"] = password_input.get('name') or 'password'

    login_submissions = [c for c in captures_list if c.method == 'POST' and ('login' in (c.url or '').lower() or 'login' in (c.path or '').lower())]
    if login_submissions:
        submission = login_submissions[0]
        headers = submission.headers if isinstance(submission.headers, dict) else {}
        body = submission.body or ''
        auth_analysis["submit_headers"] = dict(headers)

        is_ajax = headers.get('X-Requested-With') == 'XMLHttpRequest' or (isinstance(body, str) and 'ajax' in body.lower())
        if is_ajax:
            auth_analysis["method"] = "form_based_ajax"
            auth_analysis["submit_headers"]["X-Requested-With"] = "XMLHttpRequest"
            auth_analysis["submit_headers"]["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

        cookies_before = submission.cookies if isinstance(submission.cookies, dict) else {}
        submission_index = captures_list.index(submission)
        if submission_index + 1 < len(captures_list):
            next_capture = captures_list[submission_index + 1]
            cookies_after = next_capture.cookies if isinstance(next_capture.cookies, dict) else {}

            new_cookies = set(cookies_after.keys()) - set(cookies_before.keys())
            for cookie_name in new_cookies:
                if 'session' in cookie_name.lower() or 'sess' in cookie_name.lower():
                    auth_analysis["session_cookie"] = cookie_name
                    auth_analysis["required_cookies"].append(cookie_name)

    return auth_analysis


def analyze_request_patterns(captures):
    """Analyze request patterns - required headers, cookie dependencies"""
    patterns = {
        "required_headers": set(),
        "cookie_dependencies": {},
        "common_headers": {}
    }

    for capture in captures:
        headers = capture.headers if isinstance(capture.headers, dict) else {}
        cookies = capture.cookies if isinstance(capture.cookies, dict) else {}

        for header_name in headers.keys():
            patterns["required_headers"].add(header_name)

        if cookies:
            path = capture.path or ''
            if path not in patterns["cookie_dependencies"]:
                patterns["cookie_dependencies"][path] = set()
            patterns["cookie_dependencies"][path].update(cookies.keys())

    patterns["required_headers"] = list(patterns["required_headers"])
    patterns["cookie_dependencies"] = {
        path: list(cookies_set)
        for path, cookies_set in patterns["cookie_dependencies"].items()
    }

    return patterns


def analyze_response_patterns(captures):
    """Analyze response patterns - success/error indicators"""
    patterns = {
        "success_indicators": [],
        "error_patterns": {
            "access_denied": [],
            "session_expired": [],
            "authentication_required": []
        }
    }

    for capture in captures:
        response_lower = capture.response_body.lower() if capture.response_body else ""

        # Success indicators
        if capture.status_code == 200:
            if any(word in response_lower[:1000] for word in ['dashboard', 'welcome', 'home', 'tickets']):
                patterns["success_indicators"].append(f"Status 200 with content: {capture.path}")

        # Error patterns
        if 'access denied' in response_lower or capture.status_code == 403:
            patterns["error_patterns"]["access_denied"].append({
                "url": capture.url,
                "status": capture.status_code
            })

        if 'session expired' in response_lower or 'login' in response_lower[:500]:
            if capture.status_code in [302, 401]:
                patterns["error_patterns"]["session_expired"].append({
                    "url": capture.url,
                    "status": capture.status_code
                })

    return patterns


def analyze_forms(captures):
    """Analyze form structures from captures"""
    forms = {}

    for capture in captures:
        if capture.response_body and capture.method == 'GET':
            soup = BeautifulSoup(capture.response_body, 'html.parser')
            form = soup.find('form')

            if form:
                form_action = form.get('action') or capture.url
                form_method = form.get('method', 'POST').upper()

                fields = {}
                for input_field in form.find_all('input'):
                    field_name = input_field.get('name')
                    field_type = input_field.get('type', 'text')
                    required = input_field.has_attr('required')

                    if field_name:
                        fields[field_name] = {
                            "type": field_type,
                            "required": required
                        }

                forms[form_action] = {
                    "action": form_action,
                    "method": form_method,
                    "fields": fields
                }

    return forms


def analyze_cookies(captures):
    """Analyze cookie usage patterns"""
    cookie_analysis = {
        "all_cookies": set(),
        "session_cookies": [],
        "csrf_tokens": [],
        "cookie_lifecycle": {}
    }

    for capture in captures:
        cookies = capture.cookies if isinstance(capture.cookies, dict) else {}
        if not cookies:
            continue

        cookie_analysis["all_cookies"].update(cookies.keys())

        for cookie_name in cookies.keys():
            if 'session' in cookie_name.lower() or 'sess' in cookie_name.lower():
                if cookie_name not in cookie_analysis["session_cookies"]:
                    cookie_analysis["session_cookies"].append(cookie_name)

            if 'csrf' in cookie_name.lower() or 'token' in cookie_name.lower():
                if cookie_name not in cookie_analysis["csrf_tokens"]:
                    cookie_analysis["csrf_tokens"].append(cookie_name)

        for cookie_name, cookie_value in cookies.items():
            if cookie_name not in cookie_analysis["cookie_lifecycle"]:
                cookie_analysis["cookie_lifecycle"][cookie_name] = []
            cookie_analysis["cookie_lifecycle"][cookie_name].append({
                "timestamp": capture.captured_at.isoformat() if capture.captured_at else '',
                "url": capture.url,
                "present": True
            })

    cookie_analysis["all_cookies"] = list(cookie_analysis["all_cookies"])
    return cookie_analysis


def analyze_ajax_calls(captures):
    """Analyze AJAX/XHR calls"""
    ajax_endpoints = []

    for capture in captures:
        headers = capture.headers if isinstance(capture.headers, dict) else {}
        cookies = capture.cookies if isinstance(capture.cookies, dict) else {}
        body = capture.body or ''

        is_ajax = (
            headers.get('X-Requested-With') == 'XMLHttpRequest' or
            (isinstance(body, str) and 'ajax' in body.lower()) or
            'application/json' in headers.get('Content-Type', '')
        )

        if is_ajax:
            ajax_endpoints.append({
                "url": capture.url,
                "method": capture.method,
                "requires_auth": bool(cookies),
                "required_cookies": list(cookies.keys()),
                "headers": dict(headers),
                "body_preview": body[:200] if body else None
            })

    return ajax_endpoints


def _format_session_cookie_return(session_cookies, app_name, token_var='session_token'):
    """Helper to format session cookie return dict for generated code."""
    if session_cookies:
        primary = session_cookies[0]
        return f"'{primary}': {token_var}"
    return f"'{app_name.upper()}AUTHTOKEN': {token_var}"


def generate_handler_code(analysis, endpoint):
    """
    Generate a complete PassthroughHandler class from PolySniffer analysis.
    
    The generated handler includes:
    - process_html_response(): URL rewriting and shim injection for embedded display
    - get_upstream_cookies(): SSO/auto-login using captured auth flow
    - rewrite_upstream_body(): Optional body rewriting for API responses
    
    This is the architectural approach: handlers are generated from observed traffic,
    not hand-coded assumptions.
    """
    auth = analysis["authentication"]
    base_url = analysis["base_url"]
    cookies = analysis.get("cookie_analysis", {})
    
    endpoint_host = urlparse(endpoint.endpoint_url).netloc
    endpoint_hostname = urlparse(endpoint.endpoint_url).hostname or "app"
    app_name = re.sub(r"\W+", "_", endpoint_hostname.lower()).strip("_") or "app"
    class_name = "".join(word.title() for word in app_name.split("_")) + "PassthroughHandler"
    
    # Identify session cookies from analysis
    session_cookies = cookies.get("session_cookies", [])
    csrf_cookies = cookies.get("csrf_tokens", [])
    
    # Determine login endpoint
    login_url = auth.get("login_url") or f"{base_url}/api/v4/users/login"
    
    # Pre-compute session cookie return strings
    cached_cookie_return = _format_session_cookie_return(session_cookies, app_name, 'session_token')
    fresh_cookie_return = _format_session_cookie_return(session_cookies, app_name, 'token')
    primary_session_cookie = session_cookies[0] if session_cookies else "session_id"
    
    handler_code = f'''# Auto-generated PassthroughHandler for {app_name}
# Generated from PolySniffer analysis of {endpoint.endpoint_url}
# 
# This handler provides:
# - SSO/auto-login via get_upstream_cookies()
# - URL rewriting and shim injection via process_html_response()
# - All traffic flows through /pt/admin/{endpoint_host}/ for PolySniffer capture

import json
import logging
import re
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class {class_name}:
    """
    Passthrough handler for {app_name}.
    Generated from PolySniffer captures - do not hand-edit.
    Regenerate from fresh captures if behavior changes.
    """

    def process_html_response(self, html_str, request, endpoint_url=None, *args, **kwargs):
        """
        Process upstream HTML for embedded display in PolySaaS admin.
        - Strips problematic tags (<base>, meta redirects, CSP)
        - Injects client-side shim for URL rewriting
        - Rewrites asset URLs to go through proxy
        """
        logger.info("[{class_name}] Processing HTML response")

        if not endpoint_url:
            return html_str, None

        origin = endpoint_url.rstrip("/")
        parsed = urlparse(origin)
        base_origin = f"{{parsed.scheme}}://{{parsed.netloc}}"

        # Strip tags that break embedded display
        html_str = self._strip_base_tags(html_str)
        html_str = self._strip_meta_redirects(html_str)
        html_str = self._strip_csp(html_str)

        # Inject client-side shim
        html_str = self._inject_client_shim(html_str, base_origin, request)

        return html_str, None

    def get_upstream_cookies(self, request):
        """
        Provide session cookies for SSO/auto-login.
        Uses credentials from TenantApp.extra_config to obtain fresh session.
        """
        try:
            from dose.models import TenantApp
            from dose.utils import get_current_tenant
            import requests as _req

            tenant = get_current_tenant(request)
            if not tenant:
                return {{}}

            ta = TenantApp.objects.filter(
                tenant=tenant, app_name='{app_name}', status='active',
            ).first()
            if not ta or not ta.extra_config:
                return {{}}

            # Check for cached session token (less than 1 hour old)
            session_token = ta.extra_config.get('{app_name}_session_token')
            session_token_time = ta.extra_config.get('{app_name}_session_token_time', 0)
            if session_token and (time.time() - session_token_time < 3600):
                return {{{cached_cookie_return}}}

            # Expired or missing - perform fresh login
            logger.info("[{class_name}] Session token expired or missing - refreshing")
            
            password = ta.extra_config.get('{app_name}_password') or ta.extra_config.get('password')
            if not password:
                logger.warning("[{class_name}] No password in extra_config")
                return {{}}

            login_id = ta.extra_config.get('{app_name}_login_id') or ta.extra_config.get('login_id') or request.user.email
            
            # Perform login
            resp = _req.post(
                '{login_url}',
                json={{'login_id': login_id, 'password': password}},
                timeout=10,
            )
            
            if resp.status_code == 200:
                # Extract session token from response header or cookies
                token = resp.headers.get('Token') or resp.cookies.get('{primary_session_cookie}')
                if token:
                    ta.extra_config['{app_name}_session_token'] = token
                    ta.extra_config['{app_name}_session_token_time'] = time.time()
                    ta.save(update_fields=['extra_config'])
                    logger.info("[{class_name}] Session token obtained and cached")
                    return {{{fresh_cookie_return}}}
            
            logger.warning("[{class_name}] Login failed: %s", resp.status_code)
        except Exception as exc:
            logger.warning("[{class_name}] get_upstream_cookies failed: %s", exc)
        return {{}}

    def rewrite_upstream_body(self, body, content_type, request, **kwargs):
        """
        Rewrite non-HTML response bodies if needed.
        Returns None to use original body, or modified bytes.
        """
        # Most API responses pass through unchanged
        return None

    def _strip_base_tags(self, html):
        """Remove <base> tags that break relative URLs in embedded context."""
        if not html:
            return html
        return re.sub(r"<base\\b[^>]*>", "", html, flags=re.IGNORECASE)

    def _strip_meta_redirects(self, html):
        """Remove meta refresh tags that navigate away from embed."""
        if not html:
            return html
        return re.sub(
            r'<meta\\s+http-equiv\\s*=\\s*["\\'"]refresh["\\'"][^>]*>',
            "", html, flags=re.IGNORECASE,
        )

    def _strip_csp(self, html):
        """Remove Content-Security-Policy meta tags."""
        if not html:
            return html
        return re.sub(
            r'<meta\\s+http-equiv\\s*=\\s*["\\'"]Content-Security-Policy["\\'"][^>]*>',
            "", html, flags=re.IGNORECASE,
        )

    def _inject_client_shim(self, html, base_origin, request):
        """
        Inject JavaScript shim that:
        - Rewrites all URLs to go through /pt/admin/{endpoint_host}/
        - Patches fetch, XHR, WebSocket to use proxy
        - Seeds session token for SPA authentication
        """
        proxy_prefix = "/pt/admin/{endpoint_host}"
        
        shim = """
<script data-polysaas-{app_name}-shim="1">
(function() {{
    var B = """ + json.dumps(base_origin) + """;  // Upstream origin
    var PROXY = """ + json.dumps(proxy_prefix) + """;  // PolySaaS proxy prefix
    var O = window.location.origin;  // PolySaaS origin
    
    // PolySaaS paths - never rewrite these
    var PS_PREFIXES = ['/static/admin/', '/static/img/', '/admin/', '/dose/', '/media/', '/accounts/', '/pt/', '/favicon'];
    function isPolySaaSPath(s) {{
        for (var i = 0; i < PS_PREFIXES.length; i++) {{
            if (s.startsWith(PS_PREFIXES[i])) return true;
        }}
        return false;
    }}
    
    // Rewrite URL to go through proxy
    function toProxy(s) {{
        if (typeof s !== 'string') return s;
        if (!s || s.startsWith('data:') || s.startsWith('blob:')) return s;
        
        // Absolute URL to upstream - rewrite to proxy
        if (s.startsWith(B)) {{
            var tail = s.slice(B.length);
            if (!tail.startsWith('/')) tail = '/' + tail;
            return PROXY + tail;
        }}
        
        // Absolute URL to PolySaaS - strip origin
        if (s.startsWith(O + '/')) s = s.slice(O.length);
        else if (s.startsWith('http:') || s.startsWith('https:') || s.indexOf('//') === 0) return s;
        
        if (s.charAt(0) !== '/') return s;
        
        // PolySaaS paths stay untouched
        if (isPolySaaSPath(s)) return s;
        
        // All other paths go through proxy
        return PROXY + s;
    }}
    
    // Patch fetch
    var _f = window.fetch;
    window.fetch = function(input, init) {{
        if (typeof input === 'string') {{
            input = toProxy(input);
        }} else if (typeof Request !== 'undefined' && input instanceof Request) {{
            var u = toProxy(input.url);
            if (u !== input.url) input = new Request(u, input);
        }}
        return _f.call(this, input, init);
    }};
    
    // Patch XMLHttpRequest
    var _xo = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {{
        var rest = Array.prototype.slice.call(arguments, 2);
        return _xo.apply(this, [method, toProxy(url)].concat(rest));
    }};
    
    // Patch WebSocket
    var _WS = WebSocket;
    window.WebSocket = function(url, protocols) {{
        if (typeof url === 'string') {{
            try {{
                var u = new URL(url, location.href);
                u.hostname = location.hostname;
                u.port = location.port || '';
                u.protocol = (location.protocol === 'https:') ? 'wss:' : 'ws:';
                if (!u.pathname.startsWith('/pt/')) {{
                    u.pathname = PROXY + u.pathname;
                }}
                url = u.toString();
                console.log('[PolySaaS] WebSocket through proxy:', url);
            }} catch(e) {{ console.log('[PolySaaS] WebSocket rewrite error:', e); }}
        }}
        return protocols === undefined ? new _WS(url) : new _WS(url, protocols);
    }};
    
    // Patch element src/href setters
    function patchProp(proto, prop) {{
        var d = Object.getOwnPropertyDescriptor(proto, prop);
        if (!d || !d.set) return;
        Object.defineProperty(proto, prop, {{
            get: d.get,
            set: function(v) {{
                if (typeof v === 'string') v = toProxy(v);
                d.set.call(this, v);
            }},
            configurable: true, enumerable: true
        }});
    }}
    patchProp(HTMLScriptElement.prototype, 'src');
    patchProp(HTMLLinkElement.prototype, 'href');
    patchProp(HTMLImageElement.prototype, 'src');
    
    // Patch setAttribute
    var _setAttr = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function(name, value) {{
        if (typeof value === 'string') {{
            var ln = name.toLowerCase();
            if ((ln === 'src' || ln === 'href') &&
                (this instanceof HTMLScriptElement || this instanceof HTMLLinkElement || this instanceof HTMLImageElement)) {{
                value = toProxy(value);
            }}
        }}
        return _setAttr.call(this, name, value);
    }};
    
    console.log('[PolySaaS] {app_name} shim loaded - all traffic routed through', PROXY);
}})();
</script>
"""
        
        # Inject shim after <head>
        lower = html.lower()
        idx = lower.find("<head>")
        if idx != -1:
            ins = idx + len("<head>")
            return html[:ins] + shim + html[ins:]
        if "</head>" in html:
            return html.replace("</head>", shim + "</head>", 1)
        return shim + html
'''

    return handler_code


def generate_handler_from_captures(endpoint_host, capture_session_id):
    """
    Return a reviewable draft generated from one completed Native session.
    """
    return analyze_polysniffer_capture(endpoint_host, capture_session_id)

