"""
Structured Capture Export for AI Consumption
Generates rich JSON payloads that are copy-paste ready for LLMs to generate handlers
"""
import json
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from django.utils import timezone


def generate_structured_capture(endpoint, traffic_logs=None):
    """
    Generate Phase 2 structured JSON payload from PolySniffer captures.
    
    This is the "ultimate reconnaissance tool" output that feeds directly into AI.
    Returns JSON that is copy-paste ready for Cursor, Claude, Grok, etc.
    """
    from .models import TrafficLog
    
    # Get all captures for this endpoint if not provided
    if traffic_logs is None:
        traffic_logs = TrafficLog.objects.filter(
            endpoint_name__icontains=endpoint.trigger_path or endpoint.endpoint_url
        ).order_by('captured_at')
    
    # Extract base URL
    parsed_url = urlparse(endpoint.endpoint_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # Detect app name from URL or endpoint
    app_name = detect_app_name(endpoint)
    
    # Analyze authentication flow
    auth_flow = analyze_auth_flow(traffic_logs, endpoint)
    
    # Analyze captured actions
    actions = analyze_actions(traffic_logs)
    
    # Detect JavaScript framework
    js_framework = detect_js_framework(traffic_logs)
    
    # Extract observed patterns
    patterns = extract_patterns(traffic_logs)
    
    structured_capture = {
        "endpoint_id": f"{endpoint.trigger_path or 'endpoint'}_{endpoint.id}",
        "app_name": app_name,
        "base_url": base_url,
        "endpoint_url": endpoint.endpoint_url,
        "auth_type": auth_flow.get("auth_type", "unknown"),
        "login_flow": auth_flow,
        "actions_captured": actions,
        "js_framework": js_framework,
        "observed_patterns": patterns,
        "capture_timestamp": timezone.now().isoformat(),
        "total_captures": len(traffic_logs) if traffic_logs else 0
    }
    
    return structured_capture


def detect_app_name(endpoint):
    """Detect application name from endpoint URL or trigger path"""
    url_lower = endpoint.endpoint_url.lower()
    path_lower = (endpoint.trigger_path or "").lower()
    
    if 'osticket' in url_lower or 'osticket' in path_lower or '/scp/' in url_lower:
        return "OS Ticket"
    elif 'gmail' in url_lower or 'gmail' in path_lower:
        return "Gmail"
    elif 'notion' in url_lower or 'notion' in path_lower:
        return "Notion"
    elif 'airtable' in url_lower or 'airtable' in path_lower:
        return "Airtable"
    elif 'github' in url_lower or 'github' in path_lower:
        return "GitHub"
    elif 'zendesk' in url_lower or 'zendesk' in path_lower:
        return "Zendesk"
    elif 'salesforce' in url_lower or 'salesforce' in path_lower:
        return "Salesforce"
    else:
        # Try to extract from domain
        parsed = urlparse(endpoint.endpoint_url)
        domain = parsed.netloc.replace('www.', '').split('.')[0]
        return domain.title() if domain else "Unknown App"


def analyze_auth_flow(traffic_logs, endpoint):
    """Analyze authentication flow from captures"""
    auth_flow = {
        "login_url": None,
        "method": None,
        "required_fields": [],
        "csrf_source": None,
        "cookies_set": [],
        "auth_type": None
    }
    
    if not traffic_logs:
        return auth_flow
    
    # Find login page
    login_logs = [log for log in traffic_logs if 'login' in log.url.lower() or 'login' in log.path.lower()]
    
    if login_logs:
        login_log = login_logs[0]
        auth_flow["login_url"] = login_log.path or login_log.url
        
        # Analyze login page HTML
        if login_log.response_body:
            soup = BeautifulSoup(login_log.response_body[:50000], 'html.parser')  # Limit size
            
            # Find form
            form = soup.find('form')
            if form:
                auth_flow["method"] = form.get('method', 'POST').upper()
                
                # Find all input fields
                for input_field in form.find_all('input'):
                    field_name = input_field.get('name')
                    field_type = input_field.get('type', 'text')
                    
                    if field_name:
                        if field_type == 'password':
                            auth_flow["required_fields"].append("passwd" if 'pass' in field_name.lower() else field_name)
                        elif field_type == 'text' and ('user' in field_name.lower() or 'email' in field_name.lower() or 'login' in field_name.lower()):
                            auth_flow["required_fields"].append("username" if 'user' in field_name.lower() else field_name)
                        elif 'csrf' in field_name.lower() or 'token' in field_name.lower():
                            auth_flow["csrf_source"] = f"input[name='{field_name}'] in DOM"
                            auth_flow["required_fields"].append(field_name)
                
                # Check if AJAX login
                if login_log.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'ajax' in (login_log.body or '').lower():
                    auth_flow["auth_type"] = "session_cookie + csrf_token_in_form (AJAX)"
                else:
                    auth_flow["auth_type"] = "session_cookie + csrf_token_in_form"
    
    # Find login submission
    login_submissions = [log for log in traffic_logs if log.method == 'POST' and ('login' in log.url.lower() or 'login' in log.path.lower())]
    
    if login_submissions:
        submission = login_submissions[0]
        
        # Track cookies before and after
        cookies_before = set(submission.cookies.keys())
        
        # Find next capture to see cookies after login
        submission_index = list(traffic_logs).index(submission) if submission in list(traffic_logs) else -1
        if submission_index >= 0 and submission_index + 1 < len(traffic_logs):
            next_log = list(traffic_logs)[submission_index + 1]
            cookies_after = set(next_log.cookies.keys())
            
            # New cookies = session cookies
            new_cookies = cookies_after - cookies_before
            auth_flow["cookies_set"] = list(new_cookies)
    
    if not auth_flow["auth_type"]:
        if auth_flow["csrf_source"]:
            auth_flow["auth_type"] = "session_cookie + csrf_token_in_form"
        elif auth_flow["cookies_set"]:
            auth_flow["auth_type"] = "session_cookie"
        else:
            auth_flow["auth_type"] = "unknown"
    
    return auth_flow


def analyze_actions(traffic_logs):
    """Analyze captured actions (form submissions, AJAX calls, etc.)"""
    actions = []
    
    if not traffic_logs:
        return actions
    
    for log in traffic_logs:
        # Skip login actions (already in auth_flow)
        if 'login' in log.url.lower() or 'login' in log.path.lower():
            continue
        
        # Only analyze POST requests (actions)
        if log.method != 'POST':
            continue
        
        action = {
            "name": extract_action_name(log),
            "url": log.path or log.url,
            "method": log.method,
            "form_selector": None,
            "csrf_field_name": None,
            "dynamic_headers": [],
            "anti_bot_triggers": []
        }
        
        # Analyze request headers
        if log.headers:
            for header_name in ['X-Requested-With', 'X-CSRF-Token', 'X-OST-RequestToken', 'X-Requested-By']:
                if header_name in log.headers:
                    action["dynamic_headers"].append(header_name)
        
        # Analyze response for form structure
        if log.response_body:
            soup = BeautifulSoup(log.response_body[:10000], 'html.parser')  # Limit size
            form = soup.find('form')
            if form:
                form_id = form.get('id')
                form_class = form.get('class')
                if form_id:
                    action["form_selector"] = f"#{form_id}"
                elif form_class:
                    action["form_selector"] = f".{form_class[0]}"
                
                # Find CSRF field
                csrf_input = form.find('input', {'name': lambda x: x and ('csrf' in x.lower() or 'token' in x.lower())})
                if csrf_input:
                    action["csrf_field_name"] = csrf_input.get('name')
        
        # Check for file uploads
        if log.body and ('multipart' in (log.headers.get('Content-Type') or '') or 'file' in log.body.lower()):
            action["multipart"] = True
            action["files"] = ["attachments[]"]  # Common pattern
        
        # Check for anti-bot triggers
        if log.response_body:
            response_lower = log.response_body.lower()
            if 'captcha' in response_lower or 'hcaptcha' in response_lower:
                action["anti_bot_triggers"].append("hCaptcha widget detected")
            if 'recaptcha' in response_lower:
                action["anti_bot_triggers"].append("reCAPTCHA widget detected")
        
        actions.append(action)
    
    return actions


def extract_action_name(log):
    """Extract human-readable action name from URL/path"""
    path = log.path or log.url
    path_lower = path.lower()
    
    if 'ticket' in path_lower and 'open' in path_lower:
        return "Create Ticket"
    elif 'ticket' in path_lower and ('reply' in path_lower or 'response' in path_lower):
        return "Reply to Ticket"
    elif 'ticket' in path_lower and 'close' in path_lower:
        return "Close Ticket"
    elif 'create' in path_lower or 'new' in path_lower:
        return "Create Item"
    elif 'update' in path_lower or 'edit' in path_lower:
        return "Update Item"
    elif 'delete' in path_lower or 'remove' in path_lower:
        return "Delete Item"
    else:
        # Use path as name
        return path.split('/')[-1].replace('.php', '').replace('.html', '').title()


def detect_js_framework(traffic_logs):
    """Detect JavaScript framework from response bodies"""
    if not traffic_logs:
        return "unknown"
    
    frameworks = []
    
    for log in traffic_logs[:10]:  # Check first 10 logs
        if log.response_body:
            body_lower = log.response_body.lower()
            
            if 'jquery' in body_lower and 'jquery' not in frameworks:
                # Try to detect version
                import re
                jq_match = re.search(r'jquery[.\-]?(\d+\.\d+)', body_lower)
                if jq_match:
                    frameworks.append(f"jQuery {jq_match.group(1)}")
                else:
                    frameworks.append("jQuery")
            
            if 'react' in body_lower and 'React' not in frameworks:
                frameworks.append("React")
            
            if 'vue' in body_lower and 'Vue' not in frameworks:
                frameworks.append("Vue")
            
            if 'angular' in body_lower and 'Angular' not in frameworks:
                frameworks.append("Angular")
    
    if frameworks:
        return " + ".join(frameworks) if len(frameworks) > 1 else frameworks[0]
    
    # Check for custom scripts
    for log in traffic_logs[:5]:
        if log.response_body and ('custom' in log.response_body.lower() or 'ost' in log.url.lower()):
            return "jQuery 1.9 + custom OST scripts"  # Common for OS Ticket
    
    return "unknown"


def extract_patterns(traffic_logs):
    """Extract observed patterns from captures"""
    patterns = []
    
    if not traffic_logs:
        return patterns
    
    # Check for token refresh patterns
    csrf_tokens = set()
    for log in traffic_logs:
        if log.body:
            # Look for CSRF tokens in POST data
            import re
            token_matches = re.findall(r'(csrf|token|authenticity)[_\-]?token[=:]\s*([a-zA-Z0-9]+)', log.body.lower())
            if token_matches:
                csrf_tokens.add(token_matches[0][1])
    
    if len(csrf_tokens) > 1:
        patterns.append("token refreshed every navigation")
    
    # Check for required cookies
    all_cookies = set()
    for log in traffic_logs:
        if log.cookies:
            all_cookies.update(log.cookies.keys())
    
    session_cookies = [c for c in all_cookies if 'session' in c.lower() or 'sess' in c.lower()]
    if session_cookies:
        patterns.append(f"{session_cookies[0]} required on all requests")
    
    # Check for AJAX patterns
    ajax_count = sum(1 for log in traffic_logs if log.headers.get('X-Requested-With') == 'XMLHttpRequest')
    if ajax_count > len(traffic_logs) * 0.5:
        patterns.append("heavy AJAX usage - most requests are XHR")
    
    return patterns


def generate_llm_prompt(structured_capture):
    """
    Generate LLM prompt from structured capture.
    This is the "Copy as LLM Prompt" button output.
    """
    prompt = f"""You are an expert reverse-engineer for PolySaaS handlers.

Generate a complete, production-ready handler for this endpoint using the capture below.

Requirements:
- Handle CSRF exactly as observed
- Preserve all cookies
- Support file uploads if present
- Use httpx + BeautifulSoup for DOM parsing
- Be multi-tenant safe
- Handle session expiration gracefully
- Support all captured actions

Capture data:

{json.dumps(structured_capture, indent=2)}

Generate Python/Django code that:
1. Implements auto-login with the exact flow captured
2. Handles all CSRF tokens and cookies correctly
3. Supports all captured actions
4. Is production-ready and handles errors gracefully
"""
    
    return prompt


def generate_grok_url(structured_capture):
    """
    Generate Grok URL with pre-filled prompt.
    This is the "Send to Grok" button functionality.
    """
    import urllib.parse
    
    prompt = generate_llm_prompt(structured_capture)
    
    # URL encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)
    
    # Grok URL format (may need adjustment based on actual Grok interface)
    grok_url = f"https://grok.com/compose?prompt={encoded_prompt}"
    
    return grok_url

