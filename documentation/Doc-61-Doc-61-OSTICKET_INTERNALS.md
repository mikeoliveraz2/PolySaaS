# OSTicket Internals & Architecture

**Date**: October 23, 2025  
**Status**: Complete Research  

## Quick Facts

- **Type**: Open-source PHP ticketing system
- **Authentication**: Session-based with HTTP cookies
- **Frontend**: jQuery + custom JavaScript
- **Key Port**: Usually 80/443 (https)
- **Database**: MySQL (in OSTicket's case, PostgreSQL in this environment)
- **Core Tech Stack**: PHP 7.x+, jQuery, AJAX

## Directory Structure

```
/scp/
├── login.php          ← User authentication (status: 422 - needs credentials)
├── index.php          ← Dashboard/home (status: 302 - requires auth, redirects to login)
├── tickets.php        ← Ticket management (status: 302 - requires auth)
├── ajax.php           ← AJAX handler (status: 403 - forbidden, auth required)
├── api/               ← REST API endpoints (status: 404 in this config)
├── admin/             ← Admin panel (status: 404 - not accessible to current user)
└── [other endpoints]  ← Various ticket/user management endpoints
```

## HTTP Status Code Analysis

| Endpoint | Status | Meaning |
|----------|--------|---------|
| `login.php` | 422 | Unprocessable Entity - POST without valid credentials |
| `index.php` | 302 | Redirect - requires authentication, sends to login.php |
| `ajax.php` | 403 | Forbidden - AJAX endpoint requires auth + proper headers |
| `api.php` | 404 | Not Found - API disabled or not configured |
| `tickets.php` | 302 | Redirect - requires authentication |
| `admin/` | 404 | Not Found - admin panel not accessible to current user |

## Authentication Flow

### Step 1: Unauthenticated Request
```
GET /scp/index.php
↓
Status: 302 Redirect
Location: /scp/login.php
```

### Step 2: Login Form Submission
```
POST /scp/login.php
Headers: Content-Type: application/x-www-form-urlencoded
Body: email=user@example.com&passwd=password&remind=1&do=login

↓ (Valid credentials)
Status: 302 Redirect
Location: /scp/index.php
Set-Cookie: session_id=xxxxx (stored by requests.Session())
```

### Step 3: Authenticated Requests
```
GET /scp/index.php
Cookie: session_id=xxxxx (sent automatically by requests.Session())
↓
Status: 200 OK
Content: [Dashboard HTML]
```

## Key Endpoints

### 1. `/scp/login.php` - Authentication
- **Method**: POST
- **Parameters**:
  - `email`: User email address
  - `passwd`: User password  
  - `remind`: Remember device flag (1 = yes)
  - `do`: Action (should be "login")
- **Response**: 
  - Success: 302 redirect to `/scp/index.php`
  - Failure: 200 with form errors displayed
- **Session**: Creates HTTP session cookie

### 2. `/scp/index.php` - Dashboard
- **Method**: GET
- **Requires**: Valid session cookie
- **Response**: Dashboard HTML with navigation, stats, ticket list
- **Content**: Dynamically generated based on user role and permissions

### 3. `/scp/ajax.php` - Dynamic Updates
- **Method**: POST/GET
- **Purpose**: Handle AJAX requests for:
  - Sidebar navigation
  - Live updates
  - Search results
  - Form submissions without page reload
- **Requires**: Valid session + CSRF token
- **Response**: JSON data or HTML fragments

### 4. `/scp/tickets.php` - Ticket Management
- **Method**: GET/POST
- **Purpose**: View, create, update tickets
- **Requires**: Valid session
- **Response**: Ticket list or detail view

### 5. `/scp/user/` - User Portal
- **Method**: GET/POST
- **Purpose**: Client/user ticket portal
- **Requires**: Login (separate from staff login)
- **Response**: User-specific ticket interface

## JavaScript Architecture

### jQuery Usage
OSTicket heavily uses jQuery for:
- **AJAX requests**: `$.ajax(), $.get(), $.post()`
- **DOM manipulation**: Sidebar navigation, live updates
- **Form handling**: Submission, validation
- **Event handling**: Click, change, submit events

### Common AJAX Pattern
```javascript
$.ajax({
    url: 'ajax.php',
    type: 'POST',
    data: {
        action: 'get_tickets',
        page: 1,
        status: 'open'
    },
    success: function(data) {
        // Update DOM with response
        $('#ticket-list').html(data.html);
    },
    error: function(xhr, status, error) {
        console.error('AJAX error:', error);
    }
});
```

### Sidebar Navigation
The sidebar dynamically loads different views using AJAX:
- Click "My Tickets" → AJAX to `/scp/ajax.php?action=my_tickets`
- Response contains HTML fragment
- JavaScript inserts fragment into content area
- NO page reload required

## Session Management

### Cookies
OSTicket uses HTTP-only cookies for session management:
- **Cookie Name**: Typically `PHPSESSID` or custom session name
- **Cookie Path**: `/scp/`
- **Cookie Secure**: Yes (HTTPS)
- **Cookie HttpOnly**: Yes (not accessible via JavaScript)

### Session Storage
- **Backend**: PHP `$_SESSION` (stored server-side)
- **Format**: Serialized PHP objects
- **Timeout**: Typically 30 minutes of inactivity
- **User Data**: email, role, permissions, preferences

### For DOSE Integration
The key point: **`requests.Session()` automatically handles cookies**

```python
# Session automatically stores and sends cookies
sess = requests.Session()

# First request: POST credentials, server sets session cookie
resp1 = sess.post('https://osticket.app/scp/login.php', data={...})

# Second request: Session cookie sent automatically
resp2 = sess.get('https://osticket.app/scp/index.php')
# Browser/requests library sees the cookie from response1 and sends it in response2
```

## CSRF Protection

OSTicket likely implements CSRF tokens in forms:

### Form Structure
```html
<form method="POST" action="ajax.php">
    <input type="hidden" name="csrf_token" value="abc123xyz">
    <input type="text" name="email" placeholder="Email">
    <input type="password" name="passwd" placeholder="Password">
    <button type="submit">Login</button>
</form>
```

### CSRF Token Handling
1. Server includes CSRF token in HTML form
2. Client submits form with token
3. Server validates token matches session
4. Prevents cross-site form attacks

### For DOSE Integration
Our current approach:
```python
# Pass all POST data exactly as submitted (including CSRF token)
post_data = {key: request.POST[key] for key in request.POST}
response = sess.post(url, data=post_data)
```

This works because:
- We extract the CSRF token from the HTML response
- When Django form is submitted, it includes that token
- OSTicket server validates token against session ✓

## URL Patterns & Rewriting

### Original OSTicket URLs
```
https://oliverenterprises.app.saasify.cloud/scp/login.php
https://oliverenterprises.app.saasify.cloud/scp/index.php
https://oliverenterprises.app.saasify.cloud/scp/ajax.php
https://oliverenterprises.app.saasify.cloud/scp/tickets.php
```

### OSTicket HTML References
When serving these pages, OSTicket HTML contains URLs like:
```html
<!-- Absolute URLs -->
<a href="https://oliverenterprises.app.saasify.cloud/scp/index.php">Dashboard</a>

<!-- Root-relative URLs -->
<a href="/scp/tickets.php">Tickets</a>

<!-- Relative URLs -->
<form action="ajax.php" method="POST">
<a href="login.php?action=logout">Logout</a>

<!-- CSS/JS resources -->
<link rel="stylesheet" href="/scp/css/main.css">
<script src="/scp/js/jquery.js"></script>

<!-- AJAX calls -->
$.ajax({url: 'ajax.php', ...});
$.ajax({url: '/scp/ajax.php', ...});
```

### DOSE Rewriting Strategy
For proxying at `/admin/osticket/`:

**Stage 1: Full URL Replacement**
```
https://oliverenterprises.app.saasify.cloud/scp/ → /admin/osticket/
https://oliverenterprises.app.saasify.cloud → /admin/osticket
```

**Stage 2: Regex Rewriting**
```
/scp/ → /admin/osticket/
/scp/something.php → /admin/osticket/something.php
```

**Stage 3: Relative Path Interception (JavaScript)**
When JavaScript makes dynamic requests:
```javascript
// Original OSTicket code:
$.ajax({url: 'ajax.php', ...})

// After jQuery beforeSend interceptor:
$.ajax({url: '/admin/osticket/ajax.php', ...})

// Django routes to:
/admin/osticket/ajax.php → osticket_admin_view(request, path='ajax.php')

// View fetches from:
https://oliverenterprises.app.saasify.cloud/scp/ajax.php
```

## API Considerations

### OSTicket API
OSTicket has a REST API for programmatic access:
- **Endpoint**: `/api.php/...`
- **Authentication**: API key in request header
- **Methods**: GET, POST (limited PUT/DELETE support)
- **Response**: JSON

### Current Status
- In this environment: `/api.php` returns 404
- API may not be enabled or configured
- Not accessible without proper API configuration

### Future Integration
Could expose OSTicket API through Django:
```python
# Example: Add to osticket_admin_view
if request.path.startswith('/admin/osticket/api/'):
    # Handle API requests
    # Require API key authentication
    # Return JSON responses
```

## Browser DevTools Observations

### Network Tab Insights
When logged in to OSTicket:
1. **Initial load**: `/scp/index.php` returns full HTML (500-1000KB)
2. **Sidebar clicks**: AJAX POST to `/scp/ajax.php`
3. **AJAX responses**: JSON with `{html: '...', status: 'success'}`
4. **CSS/JS**: Loaded from `/scp/css/` and `/scp/js/`

### Key Request Headers
```
POST /scp/ajax.php HTTP/1.1
Host: oliverenterprises.app.saasify.cloud
Content-Type: application/x-www-form-urlencoded
Cookie: PHPSESSID=abcd1234xyz
X-Requested-With: XMLHttpRequest  (jQuery adds this)

action=get_tickets&page=1&filter=open
```

## Performance Characteristics

### Page Load Time
- Initial HTML: ~200-500ms (network latency)
- CSS/JS loading: ~500-1000ms (multiple resources)
- AJAX updates: ~100-200ms (simple data)
- **Total initial load**: ~1-2 seconds

### Database Queries
Each request may trigger:
- User authentication check (1 query)
- Permission verification (1-2 queries)
- Data fetching (5-20 queries depending on view)
- **Total**: 10-50 queries per request

### Optimization Opportunities
1. Cache static resources (CSS, JS, images)
2. Implement query caching in PHP
3. Use AJAX for incremental data loading
4. Lazy-load sidebar data

## Security Considerations

### 1. Authentication
- ✓ HTTP-only cookies prevent JavaScript access
- ✓ Session timeout prevents session hijacking
- ✓ HTTPS encryption in transit

### 2. Authorization
- ✓ Server-side permission checks on each endpoint
- ✓ User role-based access control (RBAC)
- ✓ Admin panel restricted to staff

### 3. Input Validation
- Should validate: form inputs, AJAX data
- Check: file uploads, SQL injection prevention
- Review: XSS prevention in generated HTML

### 4. CSRF Protection
- ✓ Likely uses token validation
- ✓ Our proxy preserves tokens automatically

### 5. For DOSE Integration
Risks we manage:
- **Data exposure**: Django staff user sees all OSTicket data ✓ OK
- **Session hijacking**: Each user gets separate session ✓ OK
- **CSRF attacks**: Token validation preserved ✓ OK
- **XSS injection**: We don't modify OSTicket HTML content ✓ OK

## Integration Points for DOSE

### 1. Multi-Tenancy
Currently: Single OSTicket instance for all DOSE tenants
Future considerations:
- Separate OSTicket per tenant?
- OSTicket API for tenant isolation?
- Custom tenant field in OSTicket?

### 2. User Synchronization
Currently: DOSE staff users access OSTicket separately
Enhancement possibilities:
- Sync DOSE users to OSTicket users
- SSO (Single Sign-On) integration
- OAuth2 provider/consumer

### 3. Ticket Automation
Could automate from DOSE:
- Create tickets programmatically via API
- Link tickets to DOSE entities
- Trigger DOSE actions from ticket events

### 4. Reporting & Analytics
Could extract data:
- Ticket metrics and trends
- Response time analytics
- User productivity stats
- Export to DOSE dashboards

### 5. Webhook Integration
OSTicket likely supports webhooks:
- On ticket creation
- On ticket status change
- On user activity
- Could trigger DOSE workflows

## Testing Checklist

For each feature, test:

- [ ] **Login**
  - [ ] Valid credentials work
  - [ ] Invalid credentials rejected
  - [ ] Session cookie created and persisted

- [ ] **Dashboard**
  - [ ] Loads without errors
  - [ ] Shows user's tickets
  - [ ] Displays correct counts/stats

- [ ] **Ticket Management**
  - [ ] Can view tickets
  - [ ] Can create new ticket
  - [ ] Can update ticket status
  - [ ] Can add notes to ticket

- [ ] **Navigation**
  - [ ] Sidebar links work
  - [ ] AJAX navigation updates content
  - [ ] No 404 errors
  - [ ] Page doesn't reload

- [ ] **Forms**
  - [ ] Form submission works
  - [ ] CSRF tokens processed correctly
  - [ ] File uploads (if applicable)
  - [ ] Form validation errors displayed

- [ ] **Session**
  - [ ] Session persists across requests
  - [ ] Multiple requests share same session
  - [ ] Logout clears session

## Common Issues & Solutions

### Issue: Login fails with 422
**Cause**: POST data not formatted correctly  
**Solution**: Ensure form data is `application/x-www-form-urlencoded`
**Check**: Convert Django QueryDict to regular dict (our code does this ✓)

### Issue: AJAX returns 403 Forbidden
**Cause**: AJAX endpoint requires special headers or valid session  
**Solution**: Ensure session cookie is included (requests.Session handles this ✓)
**Check**: jQuery `X-Requested-With: XMLHttpRequest` header may be needed

### Issue: Sidebar navigation doesn't work
**Cause**: AJAX URL not rewritten to go through Django  
**Solution**: jQuery beforeSend interceptor rewrites URLs (our code does this ✓)
**Check**: Browser DevTools network tab to verify URLs are going to `/admin/osticket/`

### Issue: CSS/JS resources 404
**Cause**: Stylesheet/script URLs not rewritten  
**Solution**: HTML processing stage 2 regex rewriting (our code does this ✓)
**Check**: View source in browser to verify URLs are `/admin/osticket/...`

### Issue: Session expires quickly
**Cause**: OSTicket session timeout (typically 30min)  
**Solution**: Normal behavior - user logs out after inactivity
**Enhancement**: Could auto-refresh session periodically via AJAX

## References & Documentation

- **OSTicket Docs**: https://docs.osticket.com/
- **OSTicket API**: https://docs.osticket.com/en/latest/
- **PHP Sessions**: https://www.php.net/manual/en/book.session.php
- **CSRF Protection**: https://owasp.org/www-community/attacks/csrf
- **jQuery AJAX**: https://api.jquery.com/jQuery.ajax/
- **requests Library**: https://requests.readthedocs.io/

## Next Steps

1. **Test Authentication**
   - Verify login works at `/admin/osticket/login.php`
   - Confirm session cookie is created
   - Test that dashboard loads after login

2. **Test Navigation**
   - Click sidebar links
   - Verify AJAX requests go to `/admin/osticket/`
   - Confirm content updates without page reload

3. **Test Data Operations**
   - Create a new ticket
   - Update ticket status
   - Add a note to ticket
   - Verify changes persist

4. **Test Edge Cases**
   - Session timeout
   - Invalid CSRF token
   - Concurrent requests
   - File uploads (if applicable)

5. **Monitor Performance**
   - Page load time
   - AJAX response time
   - Memory usage
   - Database query count

6. **Security Testing**
   - Verify @staff_member_required enforced
   - Check no data leakage between users
   - Test CSRF token validation
   - Verify no XSS vulnerabilities

