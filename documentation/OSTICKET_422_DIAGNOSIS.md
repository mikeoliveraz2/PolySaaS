# OSTicket 422 Error Diagnosis Guide

## Current Issue
Getting HTTP 422 (Unprocessable Entity) from `https://oliverenterprises.app.saasify.cloud/scp/`

## What is 422?
- **HTTP 422**: Unprocessable Entity
- Usually means: "I understood the request, but the content is invalid"
- Not a connection error, server IS responding
- Could be: validation error, missing auth, missing headers, wrong path, etc.

## Things to Check

### 1. Test Raw Endpoint
Run the diagnostic script:
```powershell
cd c:\Users\PC\OneDrive\Documents\GitHub\DoseV3MasterSaaS-main-main
python test_raw_endpoint.py
```

This will test:
- `https://oliverenterprises.app.saasify.cloud/scp/` (current)
- `https://oliverenterprises.app.saasify.cloud/scp/login.php`
- `https://oliverenterprises.app.saasify.cloud/scp/dashboard.php`
- `https://oliverenterprises.app.saasify.cloud/` (root)
- `https://oliverenterprises.app.saasify.cloud/admin/`

### 2. Check Django Server Logs
Start Django server with verbose output:
```powershell
# In a terminal, activate venv and run:
python manage.py runserver 8000 --verbosity 3
```

Then visit `/admin/osticket/` in another terminal and check logs for:
- `[OSTICKET VIEW]` debug messages
- Full request/response details
- Error tracebacks

### 3. Verify Endpoint URL
The current endpoint is set to: `https://oliverenterprises.app.saasify.cloud/scp/`

Check if:
- Is this domain still active?
- Is `/scp/` the correct path?
- Should it be `/api/`, `/client/`, `/admin/`, etc.?
- Check git history or ask user for correct URL

### 4. Check for Required Headers
OSTicket might require:
- Authentication cookies/tokens
- Specific User-Agent
- Referer header
- X-Requested-With header
- CSRF token

View already includes:
```python
headers = {
    'User-Agent': 'Mozilla/5.0 ...',
    'Accept': 'text/html,application/xhtml+xml,...',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}
```

If OSTicket still returns 422, might need to add more headers.

### 5. Check for Authentication
If the endpoint requires login:
- Direct requests might fail without session
- May need to handle login redirect
- View uses `requests.Session()` which preserves cookies
- But might need to log in first

### 6. Database Configuration
Verify PassthroughEndpoint is configured:
```python
# The PassthroughEndpoint model stores endpoint configs
# But our current view doesn't actually use it anymore
# View directly uses REAL_BASE from code
REAL_BASE = "https://oliverenterprises.app.saasify.cloud/scp/"
```

If database config differs, it won't be used.

## Recent View Improvements

The view was updated with:
✅ Default path handling (/ → login.php)
✅ Query string support
✅ Better session management
✅ Proper headers
✅ Enhanced error logging
✅ JavaScript interception (AJAX/sidebar support)

The improvements should work once the 422 issue is resolved.

## Next Steps

1. **Run** `python test_raw_endpoint.py` to identify which endpoint URL works
2. **Check** Django logs while accessing `/admin/osticket/`
3. **Verify** the endpoint URL is correct and currently active
4. **Update** `REAL_BASE` in `dose/osticket_admin.py` if needed
5. **Add** authentication if the endpoint requires it

## Quick Checklist
- [ ] Run raw endpoint test script
- [ ] Check which endpoint URLs return 200 vs 422
- [ ] Verify the working URL
- [ ] Update REAL_BASE if needed
- [ ] Test again with corrected endpoint
- [ ] Verify sidebar navigation works

## Files Involved
- `dose/osticket_admin.py` - Main view (updated with better logging)
- `test_raw_endpoint.py` - Endpoint diagnostic
- `test_osticket_direct.py` - Another diagnostic tool
- `setup_osticket_endpoint.py` - PassthroughEndpoint config (not used by current view)

## Important Note
The Flask proxy in `dose/interactive_proxy_flask.py` uses the same endpoint and approach. If that works on port 8001 but this doesn't, the issue might be:
- Django view setup
- Request/response handling
- Template rendering
- Rather than the endpoint itself
