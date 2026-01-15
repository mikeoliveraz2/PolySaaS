# Rollback Plan - Passthrough Views

## Current Issues
1. OSTicket login form submission broken
2. Gmail API returning 404 errors
3. Complex path extraction logic in both API and Scraper views
4. Duplicate Airtable endpoints (AirTable vs airtable)

## Root Cause
Recent changes to handle `/pt/` routes have introduced:
- Inconsistent path extraction between API and Scraper views
- Complex conditional logic that's hard to debug
- Edge cases not properly handled

## Recommended Approach

### Option 1: Simplify Path Extraction (Recommended)
Create a single utility function for path extraction that both views use:

```python
def extract_pt_path(request_path, endpoint):
    """Extract external path from /pt/ routes or legacy paths"""
    if request_path.startswith('/pt/'):
        parts = request_path.strip('/').split('/')
        if len(parts) >= 3:
            # /pt/context/service/path... -> extract path after service
            return '/'.join(parts[3:]) if len(parts) > 3 else ''
    else:
        # Legacy: /admin/service/path or /dose/service/path
        trigger = endpoint.trigger_path
        if '/' not in trigger:
            if request_path.startswith('/admin/'):
                trigger_path = f'/admin/{trigger}/'
            else:
                trigger_path = f'/dose/{trigger}/'
        else:
            trigger_path = trigger
        return request_path.replace(trigger_path.rstrip('/'), '', 1).lstrip('/')
    return ''
```

### Option 2: Revert Recent Changes
Revert to a known working state and make smaller, incremental changes with testing.

### Option 3: Fix One Service at a Time
- Fix OSTicket first (most critical for demo)
- Then Gmail
- Then others

## Immediate Actions Needed
1. Test each endpoint individually
2. Add comprehensive logging
3. Simplify the path extraction logic
4. Remove duplicate endpoints

