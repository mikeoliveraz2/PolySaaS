# Doc-88-Doc-88-MONITOR_LOGGER_PASSTHROUGH_SCHEMA_FIX.md

## Commit: Fix Monitor-Logger Passthrough Schema Handling

### Date: December 8, 2025

### Problem
Monitor-Logger sidebar link was showing "Invalid passthrough endpoint or malformed URL" error. The issue was that passthrough endpoints were incorrectly defaulting to public schema lookup instead of using tenant-specific schemas.

### Root Cause
- `get_endpoint_config()` was using `request.session.get('schema_name')` which could be unreliable
- No explicit check to prevent public schema searches for tenant-only passthrough endpoints
- Missing imports causing runtime errors
- Incorrect model attribute access (`endpoint.name` instead of `endpoint.menu_title`)

### Changes Made

1. **Schema Handling Security** (`generic_passthrough_views.py`):
   - Changed from `request.session.get('schema_name')` to `getattr(request, 'schema_name', None)`
   - Added explicit check: if schema is None or 'public', return None with warning
   - Ensures passthrough endpoints are strictly tenant-only (never search public schema)

2. **Import Fixes**:
   - Added `import logging` and `logger = logging.getLogger(__name__)`
   - Added `from pathlib import Path`
   - Added `import sys` and `import importlib`

3. **Path Construction Fix**:
   - Changed `settings.BASE_DIR / 'dose' / ...` to `Path(settings.BASE_DIR) / 'dose' / ...` for Python 3.13 compatibility

4. **Model Attribute Fix**:
   - Changed `endpoint.name` to `endpoint.menu_title or endpoint.description or trigger` (PassThroughEndpoint has menu_title, not name)

5. **Debug Logging**:
   - Added logging in `get_endpoint_config()` to show schema, service_name, and endpoint lookup results

### Security Impact
- Passthrough endpoints now cannot accidentally access public schema data
- Tenant isolation is enforced at the code level
- Middleware's schema setting is properly utilized

### Testing
- Monitor-Logger now works correctly through `/pt/admin/monitor-logger/`
- Schema isolation prevents cross-tenant data access
- Debug logs confirm proper tenant schema usage

### Files Modified
- `dose/generic_passthrough_views.py`: Schema handling, imports, logging, path fixes

### Validation
- Monitor-Logger sidebar link now successfully loads the passthrough page
- No more "Invalid passthrough endpoint" errors
- Tenant schema isolation confirmed working

### Notes
This fix ensures all passthrough endpoints maintain proper tenant isolation and cannot access data from the public schema, addressing a critical security concern in the multi-tenant architecture.

### Status: ✅ IMPLEMENTED AND TESTED