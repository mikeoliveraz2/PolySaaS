# PolySniffer AI Vision - Auto-Generate Endpoint Handlers

## Goal
PolySniffer should capture enough information that an AI (like Cursor) can automatically analyze the output and generate/tailor the handler for that endpoint. **No more "access denied" errors** - the AI will understand the authentication flow, cookie requirements, CSRF tokens, headers, and form structures from PolySniffer's capture.

## Current PolySniffer Capabilities

PolySniffer currently captures:
- HTTP requests (method, URL, headers, body)
- HTTP responses (status, headers, body)
- Cookies (session cookies, CSRF tokens)
- Form submissions (POST data, form fields)
- AJAX calls (XHR, fetch, jQuery AJAX)
- Navigation flow (redirects, page transitions)

## What AI Needs to Auto-Generate Handlers

### 1. Authentication Flow Analysis
- **Login page detection** - Identify login forms, CSRF token extraction
- **Authentication method** - Form-based, AJAX, OAuth2, API key
- **Session cookie identification** - Which cookies are required for authenticated requests
- **Token extraction** - CSRF tokens, bearer tokens, API keys

### 2. Request Pattern Analysis
- **Required headers** - User-Agent, Referer, Origin, X-Requested-With
- **Cookie dependencies** - Which cookies must be present for each request type
- **Form field mapping** - Required vs optional fields, field types, validation rules
- **AJAX endpoint discovery** - All API endpoints used by the application

### 3. Response Pattern Analysis
- **Success indicators** - What responses indicate successful authentication/operations
- **Error patterns** - "Access denied", "Session expired", redirect patterns
- **Redirect chains** - Full authentication flow from login to dashboard

### 4. State Management
- **Cookie lifecycle** - When cookies are set, when they expire, when they're required
- **Session persistence** - How sessions are maintained across requests
- **CSRF token rotation** - When tokens change, how to refresh them

## Enhanced PolySniffer Output Format

```json
{
  "endpoint_analysis": {
    "base_url": "https://example.com",
    "authentication": {
      "method": "form_based_ajax",
      "login_url": "/scp/login.php",
      "csrf_token_field": "__CSRFToken__",
      "csrf_token_source": "input[name='__CSRFToken__']",
      "username_field": "userid",
      "password_field": "passwd",
      "submit_method": "POST",
      "submit_url": "/scp/login.php",
      "submit_headers": {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
      },
      "required_cookies": ["OSTSESSID", "__CSRFToken__"],
      "session_cookie": "OSTSESSID"
    },
    "request_patterns": {
      "required_headers": ["User-Agent", "Referer", "Origin"],
      "cookie_dependencies": {
        "/scp/dashboard.php": ["OSTSESSID"],
        "/scp/tickets.php": ["OSTSESSID", "__CSRFToken__"]
      },
      "ajax_endpoints": [
        {
          "url": "/scp/ajax.php",
          "method": "POST",
          "requires_auth": true,
          "required_cookies": ["OSTSESSID"]
        }
      ]
    },
    "response_patterns": {
      "success_indicators": ["dashboard", "tickets", "200 OK"],
      "error_patterns": {
        "access_denied": ["Access denied", "403", "401"],
        "session_expired": ["login", "session expired", "redirect to login"]
      }
    },
    "form_analysis": {
      "login_form": {
        "action": "/scp/login.php",
        "method": "POST",
        "fields": {
          "userid": {"type": "text", "required": true},
          "passwd": {"type": "password", "required": true},
          "__CSRFToken__": {"type": "hidden", "required": true, "source": "form"}
        },
        "submit_button": "button[type='submit']"
      }
    }
  },
  "captures": [
    {
      "timestamp": "2025-11-22T07:00:00Z",
      "type": "page_load",
      "url": "https://example.com/scp/login.php",
      "cookies": {},
      "response": {
        "status": 200,
        "csrf_token": "abc123...",
        "form_fields": ["userid", "passwd", "__CSRFToken__"]
      }
    },
    {
      "timestamp": "2025-11-22T07:00:01Z",
      "type": "form_submit",
      "url": "https://example.com/scp/login.php",
      "method": "POST",
      "headers": {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded"
      },
      "body": {
        "__CSRFToken__": "abc123...",
        "do": "scplogin",
        "userid": "user@example.com",
        "passwd": "***",
        "ajax": "1"
      },
      "cookies_before": {},
      "cookies_after": {
        "OSTSESSID": "xyz789...",
        "__CSRFToken__": "def456..."
      },
      "response": {
        "status": 200,
        "body": "success",
        "redirect": "/scp/dashboard.php"
      }
    },
    {
      "timestamp": "2025-11-22T07:00:02Z",
      "type": "authenticated_request",
      "url": "https://example.com/scp/dashboard.php",
      "method": "GET",
      "cookies": {
        "OSTSESSID": "xyz789...",
        "__CSRFToken__": "def456..."
      },
      "response": {
        "status": 200,
        "body_contains": ["dashboard", "tickets"]
      }
    }
  ]
}
```

## AI Handler Generation Process

### Step 1: Analyze PolySniffer Output
```python
def analyze_polysniffer_output(capture_data):
    """
    AI analyzes PolySniffer output and extracts:
    - Authentication flow
    - Required cookies/headers
    - Form structures
    - AJAX patterns
    """
    analysis = {
        "auth_method": detect_auth_method(capture_data),
        "csrf_token": extract_csrf_token_info(capture_data),
        "session_cookie": identify_session_cookie(capture_data),
        "required_headers": identify_required_headers(capture_data),
        "form_structure": analyze_forms(capture_data),
        "ajax_patterns": analyze_ajax_calls(capture_data)
    }
    return analysis
```

### Step 2: Generate Handler Code
```python
def generate_handler_from_analysis(analysis, endpoint):
    """
    AI generates handler code based on analysis:
    - Auto-login function
    - Cookie management
    - Request headers
    - Form submission logic
    """
    handler_code = f"""
    def auto_login_{endpoint.id}():
        # Generated from PolySniffer analysis
        session = requests.Session()

        # Step 1: Get login page and extract CSRF token
        login_page = session.get('{analysis['login_url']}')
        csrf_token = extract_csrf_token(login_page.text, '{analysis['csrf_token_source']}')

        # Step 2: Submit login form
        login_response = session.post(
            '{analysis['login_url']}',
            data={{
                '{analysis['username_field']}': endpoint.auth_username,
                '{analysis['password_field']}': endpoint.auth_password,
                '{analysis['csrf_token_field']}': csrf_token,
                'ajax': '1'
            }},
            headers={analysis['required_headers']}
        )

        # Step 3: Extract session cookie
        session_cookie = session.cookies.get('{analysis['session_cookie']}')

        # Step 4: Save to endpoint
        endpoint.discovered_subpaths['cookies'] = dict(session.cookies)
        endpoint.save()

        return session_cookie
    """
    return handler_code
```

### Step 3: Test Generated Handler
```python
def test_generated_handler(handler_code, endpoint):
    """
    AI tests the generated handler:
    - Attempts login
    - Verifies session cookie
    - Tests authenticated request
    - Confirms no "access denied"
    """
    # Execute generated handler
    result = execute_handler(handler_code, endpoint)

    # Verify success
    if result['success'] and not result.get('access_denied'):
        return True
    else:
        # Refine handler based on failure
        return refine_handler(handler_code, result['error'])
```

## Implementation Roadmap

### Phase 1: Enhanced Capture (Current)
- ✅ Capture full request/response cycles
- ✅ Capture cookies at each step
- ✅ Capture form submissions
- ✅ Capture AJAX calls

### Phase 2: Analysis Engine (Next)
- [ ] Extract authentication patterns
- [ ] Identify CSRF token sources
- [ ] Map cookie dependencies
- [ ] Analyze form structures
- [ ] Detect error patterns

### Phase 3: AI Integration (Future)
- [ ] Structured output format for AI consumption
- [ ] AI analysis endpoint
- [ ] Handler code generation
- [ ] Auto-testing and refinement

### Phase 4: Auto-Deployment (Future)
- [ ] Auto-update PassThroughEndpoint configuration
- [ ] Auto-generate atomic services
- [ ] Auto-create Instructions
- [ ] Self-healing handlers

## Example: OS Ticket Auto-Handler Generation

**PolySniffer Captures:**
1. Login page → CSRF token in `<input name="__CSRFToken__">`
2. AJAX login POST → Requires `X-Requested-With: XMLHttpRequest`
3. Response sets `OSTSESSID` cookie
4. Dashboard requires `OSTSESSID` cookie

**AI Generates:**
```python
def auto_login_osticket(endpoint):
    session = requests.Session()

    # Get CSRF token
    login_page = session.get(f"{endpoint.endpoint_url}/scp/login.php")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find("input", {"name": "__CSRFToken__"})["value"]

    # AJAX login
    session.post(
        f"{endpoint.endpoint_url}/scp/login.php",
        data={
            "__CSRFToken__": csrf_token,
            "do": "scplogin",
            "userid": endpoint.auth_username,
            "passwd": endpoint.auth_password,
            "ajax": "1"
        },
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
    )

    # Save cookies
    endpoint.discovered_subpaths['cookies'] = dict(session.cookies)
    endpoint.save()

    return session.cookies.get('OSTSESSID')
```

**Result:** No more "access denied" - handler is automatically generated from PolySniffer output!

## Benefits

1. **Zero Manual Configuration** - AI understands the endpoint from PolySniffer
2. **Self-Healing** - If authentication changes, re-run PolySniffer, AI updates handler
3. **Universal Support** - Works for any endpoint (OSTicket, Odoo, custom apps)
4. **No More Access Denied** - AI ensures all required cookies/headers are present
5. **Rapid Integration** - New endpoints integrated in minutes, not hours

## Next Steps

1. Enhance PolySniffer to output structured analysis JSON
2. Create AI analysis endpoint that processes PolySniffer output
3. Build handler code generator
4. Implement auto-testing and refinement loop
5. Integrate with PassThroughEndpoint admin for one-click handler generation

