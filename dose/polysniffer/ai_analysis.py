"""
AI Analysis Engine for PolySniffer Captures
Analyzes captured traffic and generates handler code automatically
"""
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from django.db.models import Q


def analyze_polysniffer_capture(endpoint_id):
    """
    Analyze PolySniffer captures for an endpoint and generate handler code.

    Returns structured analysis that AI can use to generate handlers.
    """
    from dose.models import PassThroughEndpoint
    from .models import TrafficLog

    endpoint = PassThroughEndpoint.objects.get(id=endpoint_id)

    # Get all captures for this endpoint
    captures = TrafficLog.objects.filter(
        endpoint_name__icontains=endpoint.trigger_path or endpoint.endpoint_url
    ).order_by('captured_at')

    if not captures.exists():
        return {
            "error": "No captures found for this endpoint",
            "suggestion": "Run PolySniffer first to capture traffic"
        }

    analysis = {
        "endpoint_id": endpoint_id,
        "endpoint_url": endpoint.endpoint_url,
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
        "method": None,  # form_based, ajax, oauth2, api_key
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

    # Find login page
    login_captures = [c for c in captures if 'login' in c.url.lower() or 'login' in c.path.lower()]
    if not login_captures:
        return auth_analysis

    login_capture = login_captures[0]
    auth_analysis["login_url"] = login_capture.url

    # Analyze login page HTML for form structure
    if login_capture.response_body:
        soup = BeautifulSoup(login_capture.response_body, 'html.parser')

        # Find login form
        form = soup.find('form')
        if form:
            auth_analysis["method"] = "form_based"
            auth_analysis["submit_url"] = form.get('action') or login_capture.url
            auth_analysis["submit_method"] = form.get('method', 'POST').upper()

            # Find CSRF token
            csrf_input = soup.find('input', {'name': re.compile(r'csrf|token', re.I)})
            if csrf_input:
                auth_analysis["csrf_token_field"] = csrf_input.get('name')
                auth_analysis["csrf_token_source"] = f"input[name='{csrf_input.get('name')}']"

            # Find username/password fields
            username_input = soup.find('input', {'type': 'text'}) or soup.find('input', {'name': re.compile(r'user|email|login', re.I)})
            password_input = soup.find('input', {'type': 'password'})

            if username_input:
                auth_analysis["username_field"] = username_input.get('name') or 'username'
            if password_input:
                auth_analysis["password_field"] = password_input.get('name') or 'password'

    # Find login submission
    login_submissions = [c for c in captures if c.method == 'POST' and ('login' in c.url.lower() or 'login' in c.path.lower())]
    if login_submissions:
        submission = login_submissions[0]
        auth_analysis["submit_headers"] = dict(submission.headers)

        # Check if it's AJAX
        if submission.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'ajax' in submission.body.lower():
            auth_analysis["method"] = "form_based_ajax"
            auth_analysis["submit_headers"]["X-Requested-With"] = "XMLHttpRequest"
            auth_analysis["submit_headers"]["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

        # Analyze cookies before and after
        cookies_before = submission.cookies
        # Find next capture to see cookies after
        submission_index = list(captures).index(submission)
        if submission_index + 1 < len(captures):
            next_capture = list(captures)[submission_index + 1]
            cookies_after = next_capture.cookies

            # Find new cookies (session cookie)
            new_cookies = set(cookies_after.keys()) - set(cookies_before.keys())
            if new_cookies:
                # Likely session cookie
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
        # Collect all headers
        for header_name in capture.headers.keys():
            patterns["required_headers"].add(header_name)

        # Track cookie usage per path
        if capture.cookies:
            path = capture.path
            if path not in patterns["cookie_dependencies"]:
                patterns["cookie_dependencies"][path] = set()
            patterns["cookie_dependencies"][path].update(capture.cookies.keys())

    # Convert sets to lists for JSON serialization
    patterns["required_headers"] = list(patterns["required_headers"])
    patterns["cookie_dependencies"] = {
        path: list(cookies)
        for path, cookies in patterns["cookie_dependencies"].items()
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
        if capture.cookies:
            cookie_analysis["all_cookies"].update(capture.cookies.keys())

            # Identify session cookies
            for cookie_name in capture.cookies.keys():
                if 'session' in cookie_name.lower() or 'sess' in cookie_name.lower():
                    if cookie_name not in cookie_analysis["session_cookies"]:
                        cookie_analysis["session_cookies"].append(cookie_name)

                # Identify CSRF tokens
                if 'csrf' in cookie_name.lower() or 'token' in cookie_name.lower():
                    if cookie_name not in cookie_analysis["csrf_tokens"]:
                        cookie_analysis["csrf_tokens"].append(cookie_name)

            # Track cookie lifecycle
            for cookie_name, cookie_value in capture.cookies.items():
                if cookie_name not in cookie_analysis["cookie_lifecycle"]:
                    cookie_analysis["cookie_lifecycle"][cookie_name] = []
                cookie_analysis["cookie_lifecycle"][cookie_name].append({
                    "timestamp": capture.captured_at.isoformat(),
                    "url": capture.url,
                    "present": True
                })

    # Convert sets to lists
    cookie_analysis["all_cookies"] = list(cookie_analysis["all_cookies"])

    return cookie_analysis


def analyze_ajax_calls(captures):
    """Analyze AJAX/XHR calls"""
    ajax_endpoints = []

    for capture in captures:
        # Check if it's an AJAX call
        is_ajax = (
            capture.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            'ajax' in capture.body.lower() if capture.body else False or
            'application/json' in capture.headers.get('Content-Type', '')
        )

        if is_ajax:
            ajax_endpoints.append({
                "url": capture.url,
                "method": capture.method,
                "requires_auth": bool(capture.cookies),
                "required_cookies": list(capture.cookies.keys()) if capture.cookies else [],
                "headers": dict(capture.headers),
                "body_preview": capture.body[:200] if capture.body else None
            })

    return ajax_endpoints


def generate_handler_code(analysis, endpoint):
    """Generate handler code from analysis"""
    auth = analysis["authentication"]

    if not auth["method"]:
        return None

    handler_code = f"""
# Auto-generated handler for {endpoint.trigger_path or endpoint.endpoint_url}
# Generated from PolySniffer analysis

import requests
from bs4 import BeautifulSoup

def auto_login_{endpoint.id}(endpoint):
    \"\"\"
    Auto-login handler generated from PolySniffer analysis.
    Endpoint: {endpoint.endpoint_url}
    \"\"\"
    session = requests.Session()
    base_url = "{analysis['base_url']}"
    login_url = "{auth['login_url'] or analysis['base_url'] + '/login.php'}"

    # Step 1: Get login page and extract CSRF token
    login_page = session.get(login_url, timeout=10)
    if login_page.status_code != 200:
        raise Exception(f"Cannot reach login page: {{{{login_page.status_code}}}}")

    soup = BeautifulSoup(login_page.text, 'html.parser')
"""

    if auth["csrf_token_field"]:
        handler_code += f"""
    # Extract CSRF token
    csrf_input = soup.find("input", {{"name": "{auth['csrf_token_field']}"}})
    if not csrf_input:
        raise Exception("CSRF token not found in login page")
    csrf_token = csrf_input["value"]
"""
    else:
        handler_code += """
    csrf_token = None  # No CSRF token detected
"""

    handler_code += """
    # Step 2: Submit login form
    login_data = {
"""

    if auth["username_field"]:
        handler_code += f'        "{auth["username_field"]}": endpoint.auth_username,\n'
    if auth["password_field"]:
        handler_code += f'        "{auth["password_field"]}": endpoint.auth_password,\n'
    if auth["csrf_token_field"]:
        handler_code += f'        "{auth["csrf_token_field"]}": csrf_token,\n'

    # Check if AJAX login
    if auth["method"] == "form_based_ajax":
        handler_code += '        "ajax": "1",\n'
        if "do" not in str(auth.get("submit_url", "")):
            handler_code += '        "do": "scplogin",\n'

    handler_code += """    }

    login_headers = {
"""

    for header_name, header_value in auth["submit_headers"].items():
        handler_code += f'        "{header_name}": "{header_value}",\n'

    submit_url = auth.get('submit_url') or login_url
    handler_code += f"""    }}

    login_response = session.post(
        "{submit_url}",
        data=login_data,
        headers=login_headers,
        timeout=10
    )

    # Step 3: Verify login success
    if login_response.status_code != 200:
        raise Exception(f"Login failed: {{{{login_response.status_code}}}}")

    # Step 4: Extract session cookie
"""

    if auth["session_cookie"]:
        handler_code += f"""
    session_cookie = session.cookies.get("{auth['session_cookie']}")
    if not session_cookie:
        raise Exception("Session cookie '{auth['session_cookie']}' not found after login")
"""
    else:
        handler_code += """
    # Session cookie not detected - using all cookies
    session_cookie = dict(session.cookies)
"""

    handler_code += f"""
    # Step 5: Save cookies to endpoint
    if not endpoint.discovered_subpaths:
        endpoint.discovered_subpaths = {{}}
    endpoint.discovered_subpaths['cookies'] = dict(session.cookies)
    endpoint.save()

    return session_cookie
"""

    return handler_code


def generate_handler_from_captures(endpoint_id):
    """
    Main entry point: Analyze captures and generate handler code.
    Returns analysis + generated code.
    """
    analysis = analyze_polysniffer_capture(endpoint_id)
    return analysis

